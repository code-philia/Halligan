from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any

from halligan.runtime.registry import ToolRegistry


@dataclass(frozen=True)
class ToolCapability:
    """
    A tool capability exposed via the MCP-lite interface.

    This is metadata only: it is safe to serialize and embed into prompts.
    """

    name: str
    description: str
    params: list[str]


def _safe_doc(fn: Any) -> str:
    doc = inspect.getdoc(fn) or ""
    # Keep it short; long docstrings are not prompt-friendly.
    return " ".join(doc.split())


def capabilities_from_registry(registry: ToolRegistry) -> list[ToolCapability]:
    """
    Build a stable list of tool capabilities from a registry.

    Notes
    - This does NOT attempt to serialize complex types. The goal is to provide
      discoverability ("what can I call?") rather than full type reflection.
    - Parameter names are extracted from Python signatures, excluding `self`.
    """
    caps: list[ToolCapability] = []
    for name in registry.names():
        spec = registry.get(name)
        if not spec:
            continue
        try:
            sig = inspect.signature(spec.fn)
            params = [p.name for p in sig.parameters.values() if p.name != "self"]
        except Exception:
            params = []

        caps.append(
            ToolCapability(
                name=name,
                description=_safe_doc(spec.fn),
                params=params,
            )
        )
    return caps
