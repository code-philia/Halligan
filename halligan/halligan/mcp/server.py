from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from halligan.mcp.capabilities import ToolCapability, capabilities_from_registry
from halligan.mcp.errors import MCPJSONRPCError, MCPMethodNotFound, MCPToolNotFound
from halligan.mcp.policy import MCPPolicy
from halligan.mcp.protocol import JSONRPCRequest, make_jsonrpc_error, make_jsonrpc_result, parse_jsonrpc_request
from halligan.mcp.resources import ResourceStore
from halligan.runtime.errors import ToolError
from halligan.runtime.registry import ToolRegistry


@dataclass(frozen=True)
class MCPContext:
    """
    Execution context for MCP-lite.

    In-process usage can pass arbitrary Python objects through this context.
    For stdio/networked deployments, args/results must be JSON-serializable.
    """

    policy: MCPPolicy


class InProcessMCPServer:
    """
    In-process MCP-lite server.

    This is the recommended mode for the current repository because many tools
    operate over in-memory Python objects (Frame/Element/Point).
    """

    def __init__(
        self,
        *,
        registry: ToolRegistry | None = None,
        resources: ResourceStore | None = None,
        policy: MCPPolicy | None = None,
    ) -> None:
        self._registry = registry
        self._resources = resources
        self._policy = policy or MCPPolicy(allowed_tools=set(registry.names()) if registry else None)

    # -----------------------
    # Direct (Python) methods
    # -----------------------
    def list_tools(self) -> list[ToolCapability]:
        if not self._registry:
            return []
        return capabilities_from_registry(self._registry)

    def call_tool(self, name: str, args: dict[str, Any] | None = None) -> Any:
        if not self._registry:
            raise MCPToolNotFound(name)
        if not isinstance(name, str) or not name:
            raise MCPToolNotFound(name)

        self._policy.check_tool(name)

        spec = self._registry.get(name)
        if not spec:
            raise MCPToolNotFound(name)

        args = args or {}
        if not isinstance(args, dict):
            raise ToolError("MCP tool args must be an object")

        try:
            return spec.fn(**args)
        except Exception as exc:
            # Keep ToolError as the semantic error type for executor callers.
            raise ToolError(f"MCP tool call failed: {name}: {exc}") from exc

    def list_resources(self) -> list[dict[str, str]]:
        return self._resources.list() if self._resources else []

    def read_resource(self, uri: str) -> Any:
        if not self._resources:
            raise MCPMethodNotFound("resources/read")
        return self._resources.read(uri)

    # -----------------------
    # JSON-RPC handler
    # -----------------------
    def handle(self, payload: Any) -> dict[str, Any]:
        """
        Handle a single JSON-RPC request object and return a JSON-RPC response.

        This is primarily used by the prompt-session loop, where the model emits
        a JSON request and the runtime replies with a JSON result/error.
        """
        request_id: str | int | None = payload.get("id") if isinstance(payload, dict) else None
        try:
            req: JSONRPCRequest = parse_jsonrpc_request(payload)
            request_id = req.id
            result = self._dispatch(req)
            return make_jsonrpc_result(request_id=req.id, result=result)

        except MCPJSONRPCError as exc:
            return make_jsonrpc_error(request_id=request_id, code=exc.code, message=exc.message, data=exc.data)

        except Exception as exc:
            # Hard fallback: never crash the host process due to MCP wiring.
            return make_jsonrpc_error(request_id=None, code=-32000, message="Internal MCP server error", data=str(exc))

    def _dispatch(self, req: JSONRPCRequest) -> Any:
        method = req.method
        params = req.params

        if method == "tools/list":
            return [cap.__dict__ for cap in self.list_tools()]

        if method == "tools/call":
            name = params.get("name")
            args = params.get("args", {})
            return self.call_tool(name, args=args)

        if method == "resources/list":
            return self.list_resources()

        if method == "resources/read":
            uri = params.get("uri")
            return self.read_resource(uri)

        if method == "ping":
            return {"ok": True}

        raise MCPMethodNotFound(method)
