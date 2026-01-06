from __future__ import annotations

from typing import Any

from halligan.agents import Agent
from halligan.mcp.client import InProcessMCPClient
from halligan.runtime.errors import ParseError
from halligan.runtime.parser import parse_json_from_response


def _extract_mcp_call(data: Any) -> tuple[str, dict[str, Any]] | None:
    """
    Detect whether a parsed JSON payload is an MCP request.

    Supported shapes:
      1) Wrapper form (recommended for prompts to avoid schema collisions):
         {"mcp": {"method": "...", "params": {...}}}

      2) Raw JSON-RPC request:
         {"jsonrpc": "2.0", "id": 1, "method": "...", "params": {...}}
    """
    if not isinstance(data, dict):
        return None

    if "mcp" in data:
        inner = data.get("mcp")
        if not isinstance(inner, dict):
            return None
        method = inner.get("method")
        params = inner.get("params", {}) or {}
        if isinstance(method, str) and isinstance(params, dict):
            return method, params
        return None

    if data.get("jsonrpc") == "2.0" and isinstance(data.get("method"), str):
        params = data.get("params", {}) or {}
        if not isinstance(params, dict):
            return None
        return data["method"], params

    return None


def request_json_with_mcp(
    *,
    agent: Agent,
    prompt: str,
    images: list,
    image_captions: list[str],
    mcp: InProcessMCPClient,
    stage_name: str,
    max_mcp_rounds: int = 3,
    allowed_methods: tuple[str, ...] = ("resources/read", "resources/list", "tools/list"),
) -> Any:
    """
    Request JSON from the agent with an optional MCP "context-as-resource" loop.

    Why this exists
    - Stage prompts become shorter and more stable (less token blow-up).
    - The model can pull *just enough* context via read-only resources.

    Security properties
    - Only *read-only* MCP methods are allowed by default (no tool execution).
    - Resource content should already be policy-clipped by the MCP layer.

    Returns:
        The first non-MCP JSON object produced by the agent (caller validates it
        using stage-specific schema validators).
    """
    current_prompt = prompt
    last_error: Exception | None = None

    for mcp_round in range(max_mcp_rounds + 1):
        # Never accumulate hidden chat history across retries; keep execution
        # deterministic and prevent token blow-up from unbounded context growth.
        agent.reset()
        response, _ = agent(current_prompt, images, image_captions)
        try:
            data = parse_json_from_response(response)
        except ParseError as exc:
            # Parsing failures are handled by the caller (stage loop) because it
            # wants to preserve its existing retry behavior and error messages.
            last_error = exc
            break

        mcp_call = _extract_mcp_call(data)
        if not mcp_call:
            return data

        if mcp_round >= max_mcp_rounds:
            last_error = RuntimeError(f"{stage_name}: exceeded max MCP rounds ({max_mcp_rounds})")
            break

        method, params = mcp_call
        if method not in allowed_methods:
            # Treat this as a hard error: we do not want the model to learn that
            # it can side-step the executor by invoking tools directly.
            last_error = RuntimeError(f"{stage_name}: MCP method not allowed in prompt session: {method!r}")
            break

        # Execute and append the compact response to the prompt.
        mcp_resp = mcp.request_compact(method=method, params=params, request_id=mcp_round + 1)
        current_prompt = (
            current_prompt
            + "\n\n"
            + "## MCP Response (read-only)\n"
            + f"- Request: {method} {params}\n"
            + f"- Response: {mcp_resp}\n"
            + "\n"
            + "Continue. If you need more context, emit another MCP request. Otherwise, output the final JSON."
        )

    # If we get here, something went wrong before returning a JSON object.
    raise last_error if last_error else RuntimeError(f"{stage_name}: failed to obtain JSON from agent")
