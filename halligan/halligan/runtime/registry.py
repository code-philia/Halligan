from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

ToolFn = Callable[..., Any]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    fn: ToolFn


class ToolRegistry:
    """
    A strict allowlist of callable tools that Stage 3 is permitted to invoke.

    The executor resolves tools by name from this registry. Anything not registered
    cannot be executed.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, name: str, fn: ToolFn) -> None:
        self._tools[name] = ToolSpec(name=name, fn=fn)

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools.keys())


def build_default_registry() -> ToolRegistry:
    """
    Build the default registry of safe callable tools.

    Note: Methods/properties on objects (e.g., SlideChoice.refine) are not
    registered here; those are handled separately by the executor under a
    method allowlist.
    """

    # Import lazily to avoid heavy imports during test collection.
    import halligan.utils.action_tools as action_tools
    import halligan.utils.vision_tools as vision_tools

    reg = ToolRegistry()

    # Action tools (browser interactions)
    reg.register("click", action_tools.click)
    reg.register("get_all_choices", action_tools.get_all_choices)
    reg.register("drag", action_tools.drag)
    reg.register("draw", action_tools.draw)
    reg.register("enter", action_tools.enter)
    reg.register("point", action_tools.point)
    reg.register("select", action_tools.select)
    reg.register("slide_x", action_tools.slide_x)
    reg.register("slide_y", action_tools.slide_y)
    reg.register("explore", action_tools.explore)

    # Vision tools (visual reasoning helpers)
    reg.register("mark", vision_tools.mark)
    reg.register("focus", vision_tools.focus)
    reg.register("ask", vision_tools.ask)
    reg.register("rank", vision_tools.rank)
    reg.register("compare", vision_tools.compare)
    reg.register("match", vision_tools.match)

    return reg
