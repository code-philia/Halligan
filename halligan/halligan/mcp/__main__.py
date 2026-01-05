"""
Stdio entrypoint for MCP-lite.

This is intentionally minimal and best-effort. In the current repository most
tools operate on in-memory Python objects, so in-process MCP is the primary
deployment mode.

Usage (diagnostic / introspection):
  python -m halligan.mcp

Then send one JSON-RPC request per line (e.g.):
  {"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
"""

from __future__ import annotations

import json
import sys

from halligan.mcp.client import InProcessMCPClient
from halligan.mcp.policy import MCPPolicy
from halligan.mcp.resources import ResourceStore
from halligan.mcp.server import InProcessMCPServer


def main() -> int:
    # No frames/config are available at this entrypoint; expose only static resources.
    policy = MCPPolicy()
    resources = ResourceStore.build(policy=policy)
    server = InProcessMCPServer(resources=resources, policy=policy)
    client = InProcessMCPClient(server)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except Exception as exc:
            sys.stdout.write(
                json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}) + "\n"
            )
            sys.stdout.flush()
            continue

        resp = server.handle(payload)
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()

        # Allow clients to terminate cleanly.
        if isinstance(payload, dict) and payload.get("method") in {"exit", "quit"}:
            break

    # Silence unused variable warning (client kept for symmetry / future extension).
    _ = client
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
