from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from halligan.runtime.errors import HalliganError


class MCPError(HalliganError):
    """Base class for MCP-layer errors."""


@dataclass(frozen=True)
class MCPJSONRPCError(MCPError):
    """
    A JSON-RPC shaped error.

    We keep the structure explicit so the caller can either:
    - surface a readable exception (Python), or
    - serialize it back to a JSON-RPC error object.
    """

    code: int
    message: str
    data: Any | None = None

    def __str__(self) -> str:  # pragma: no cover (tiny helper)
        base = f"[{self.code}] {self.message}"
        return base if self.data is None else f"{base} ({self.data!r})"


class MCPProtocolError(MCPJSONRPCError):
    """Raised when the incoming request is malformed."""

    def __init__(self, message: str, *, data: Any | None = None) -> None:
        super().__init__(-32600, message, data)


class MCPMethodNotFound(MCPJSONRPCError):
    """Raised when the request method is unknown."""

    def __init__(self, method: str) -> None:
        super().__init__(-32601, f"Method not found: {method!r}", {"method": method})


class MCPInvalidParams(MCPJSONRPCError):
    """Raised when the request parameters are invalid."""

    def __init__(self, message: str, *, data: Any | None = None) -> None:
        super().__init__(-32602, message, data)


class MCPPolicyError(MCPJSONRPCError):
    """Raised when a request is denied by policy."""

    def __init__(self, message: str, *, data: Any | None = None) -> None:
        super().__init__(-32001, message, data)


class MCPResourceNotFound(MCPJSONRPCError):
    """Raised when a requested resource URI does not exist."""

    def __init__(self, uri: str) -> None:
        super().__init__(-32004, f"Resource not found: {uri!r}", {"uri": uri})


class MCPToolNotFound(MCPJSONRPCError):
    """Raised when a requested tool name does not exist."""

    def __init__(self, name: str) -> None:
        super().__init__(-32005, f"Tool not found: {name!r}", {"name": name})
