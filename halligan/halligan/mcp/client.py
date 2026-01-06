from __future__ import annotations

from typing import Any

from halligan.mcp.protocol import dumps_compact
from halligan.mcp.server import InProcessMCPServer


class InProcessMCPClient:
    """
    In-process MCP-lite client.

    The client is a thin wrapper that:
    - provides a stable API for callers (stages/executor),
    - and allows swapping the transport later (e.g., stdio).
    """

    def __init__(self, server: InProcessMCPServer) -> None:
        self._server = server

    # --------
    # Tools
    # --------
    def list_tools(self) -> list[dict[str, Any]]:
        return [cap.__dict__ for cap in self._server.list_tools()]

    def call_tool(self, name: str, args: dict[str, Any] | None = None) -> Any:
        return self._server.call_tool(name, args=args or {})

    # ----------
    # Resources
    # ----------
    def list_resources(self) -> list[dict[str, str]]:
        return self._server.list_resources()

    def read_resource(self, uri: str) -> Any:
        return self._server.read_resource(uri)

    # -----------
    # JSON-RPC
    # -----------
    def request(
        self, *, method: str, params: dict[str, Any] | None = None, request_id: str | int | None = 1
    ) -> dict[str, Any]:
        """
        Send a JSON-RPC request and return the raw JSON-RPC response.

        This is used when the *model* emits an MCP request object, and we want to
        embed the result back into the prompt in a structured way.
        """
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
        return self._server.handle(payload)

    def request_compact(
        self, *, method: str, params: dict[str, Any] | None = None, request_id: str | int | None = 1
    ) -> str:
        """Convenience helper to embed a compact response into a prompt."""
        return dumps_compact(self.request(method=method, params=params, request_id=request_id))
