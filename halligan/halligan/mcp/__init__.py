"""
MCP-inspired integration layer (MCP-lite).

This package implements the design sketched in `docs/problem.md`:
- Treat tools as *controlled capabilities* (interface-first).
- Enforce policy at a single choke point (policy-first).
- Expose runtime context as queryable resources (context-as-resource).

Important scope note
This implementation is intentionally "MCP-lite": it follows the MCP *shape*
(tools/resources, request/response, auditable boundaries) without depending on
external MCP SDKs or networked services. The in-process client/server are meant
to (1) validate the architecture end-to-end, and (2) be an easy stepping stone
to a true multi-process tool server if/when needed.
"""

from .client import InProcessMCPClient
from .resources import ResourceStore
from .server import InProcessMCPServer

__all__ = [
    "InProcessMCPClient",
    "InProcessMCPServer",
    "ResourceStore",
]
