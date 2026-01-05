from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from halligan.mcp.errors import MCPPolicyError


@dataclass(frozen=True)
class MCPPolicy:
    """
    Policy-first enforcement for MCP-lite.

    This is the *single choke point* for:
    - which tools can be called,
    - which resources can be read,
    - and how much data can be returned to the model.

    The goal is to prevent "capability creep": adding MCP should not widen the
    attack surface or reintroduce ambient authority.
    """

    allowed_tools: set[str] | None = None
    allowed_resource_prefixes: tuple[str, ...] = ("mcp://",)
    max_resource_chars: int = 8_000

    def check_tool(self, name: str) -> None:
        if self.allowed_tools is None:
            return
        if name not in self.allowed_tools:
            raise MCPPolicyError("Tool not allowed by policy", data={"tool": name})

    def check_resource_uri(self, uri: str) -> None:
        if not uri or not isinstance(uri, str):
            raise MCPPolicyError("Invalid resource uri", data={"uri": uri})
        if not uri.startswith(self.allowed_resource_prefixes):
            raise MCPPolicyError("Resource uri prefix denied by policy", data={"uri": uri})

    def clip_resource(self, value: Any) -> Any:
        """
        Clip large resource payloads to reduce token blow-up.

        We only apply clipping to strings (which are the typical prompt payload).
        Structured JSON should stay structured to keep it machine-checkable.
        """
        if isinstance(value, str) and len(value) > self.max_resource_chars:
            return value[: self.max_resource_chars] + "\n...[truncated]..."
        return value
