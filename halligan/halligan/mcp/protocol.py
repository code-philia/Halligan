from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from halligan.mcp.errors import MCPInvalidParams, MCPProtocolError

JSONRPC_VERSION: Literal["2.0"] = "2.0"
JSONValue = Any


@dataclass(frozen=True)
class JSONRPCRequest:
    """
    Minimal JSON-RPC 2.0 request representation.

    We intentionally keep this small; the MCP-lite server only needs `method`,
    `params`, and `id`.
    """

    method: str
    params: dict[str, Any]
    id: str | int | None = None


def _require_dict(value: Any, *, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MCPProtocolError(f"Expected object at {path}, got {type(value).__name__}", data={"path": path})
    return value


def parse_jsonrpc_request(obj: Any) -> JSONRPCRequest:
    """
    Parse and validate a JSON-RPC request.

    Raises:
        MCPProtocolError: for malformed payloads.
        MCPInvalidParams: for invalid field values.
    """
    req = _require_dict(obj, path="$")

    version = req.get("jsonrpc", JSONRPC_VERSION)
    if version != JSONRPC_VERSION:
        raise MCPInvalidParams("Invalid jsonrpc version", data={"expected": JSONRPC_VERSION, "got": version})

    method = req.get("method")
    if not isinstance(method, str) or not method:
        raise MCPInvalidParams("method must be a non-empty string")

    params = req.get("params", {})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        raise MCPInvalidParams("params must be an object")

    req_id = req.get("id")
    if req_id is not None and not isinstance(req_id, (str, int)):
        raise MCPInvalidParams("id must be string|int|null")

    return JSONRPCRequest(method=method, params=params, id=req_id)


def make_jsonrpc_result(*, request_id: str | int | None, result: Any) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def make_jsonrpc_error(
    *, request_id: str | int | None, code: int, message: str, data: Any | None = None
) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "error": err}


def dumps_compact(obj: Any) -> str:
    """
    Produce a stable, compact JSON string.

    This is used when embedding MCP responses back into prompts, where token
    efficiency matters.
    """
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
