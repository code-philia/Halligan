from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from halligan.runtime.errors import ToolError, ValidationError
from halligan.runtime.registry import ToolRegistry
from halligan.runtime.schemas import Stage2Plan, Stage3Program

if TYPE_CHECKING:
    from halligan.utils.layout import Frame


class ToolInvoker(Protocol):
    """
    Abstract tool-invocation interface.

    Why this exists
    - Enables "MCP-lite" integration: the executor can route tool calls through a
      policy/audit layer without changing the program semantics.
    - Keeps the executor deterministic: the program is still interpreted locally,
      but capability enforcement is centralized.
    """

    def call_tool(self, name: str, args: dict[str, Any] | None = None) -> Any:  # pragma: no cover (interface)
        raise NotImplementedError


def _collect_interactables(frames: list["Frame"]) -> tuple[set[str], int]:
    """
    Collect all interactable types across the frame tree.

    Returns:
        types: set of interactable type names (strings)
        next_count: number of NEXT interactables observed
    """
    types: set[str] = set()
    next_count = 0

    queue: list["Frame"] = list(frames)
    while queue:
        frame = queue.pop(0)
        if frame.interactable:
            types.add(frame.interactable)
            if frame.interactable == "NEXT":
                next_count += 1

        # Elements on this frame
        for el in getattr(frame, "interactables", []) or []:
            if el.interactable:
                types.add(el.interactable)
                if el.interactable == "NEXT":
                    next_count += 1

        # Recurse into subframes
        for sub in getattr(frame, "subframes", []) or []:
            queue.append(sub)

    return types, next_count


def apply_stage2_plan(frames: list["Frame"], plan: Stage2Plan) -> None:
    """
    Execute Stage 2 (structure abstraction) actions in a safe, deterministic way.
    """
    for action in plan.actions:
        payload = action.payload
        frame_id = payload["frame"]
        frame = frames[frame_id]

        if action.type == "set_frame":
            frame.set_frame_as(payload["interactable"])

        elif action.type == "split_frame":
            subframes = frame.split(rows=payload["rows"], columns=payload["columns"])
            for sub in subframes:
                sub.set_frame_as(payload["mark_as"])

        elif action.type == "grid_frame":
            grid = frame.grid(tiles=payload["tiles"])
            for row in grid:
                for element in row:
                    element.set_element_as(payload["mark_as"])

        elif action.type == "get_element":
            element = frame.get_element(position=payload["position"], details=payload["details"])
            element.set_element_as(payload["mark_as"])

        else:
            raise ValidationError(f"Unknown Stage 2 action: {action.type}")

    # Post-validate structure abstraction constraints (research prototype assumptions)
    types, next_count = _collect_interactables(frames)

    non_next = {t for t in types if t != "NEXT"}
    if len(non_next) != 1:
        raise ValidationError(
            "Stage 2 must result in exactly one non-NEXT interactable type " f"(found: {sorted(non_next)})"
        )
    if next_count > 1:
        raise ValidationError("Stage 2 must have at most one NEXT interactable")


class _Break(Exception):
    pass


_ALLOWED_METHODS: dict[str, set[str]] = {
    # Layout / selection helpers
    "Frame": {"show_keypoints", "get_keypoint", "get_interactable"},
    "Point": {"show_neighbours", "get_neighbour"},
    # Action choice objects
    "SelectChoice": {"select"},
    "SlideChoice": {"refine", "release"},
    "SwapChoice": {"swap"},
    "DragChoice": {"drop"},
    "Choice": {"release"},
}


def _class_name(obj: Any) -> str:
    return obj.__class__.__name__


def _ensure_allowed_method(obj: Any, method: str) -> None:
    cls = _class_name(obj)
    allowed = _ALLOWED_METHODS.get(cls, set())
    if method not in allowed:
        raise ToolError(f"Method not allowed: {cls}.{method}")


def _eval_expr(expr: Any, *, env: dict[str, Any], frames: list["Frame"]) -> Any:
    """
    Evaluate an expression used by the Stage 3 restricted DSL.

    Expressions are JSON values with special forms:
    - {"var": "x"}
    - {"ref": "frame", "id": 0}
    - {"ref": "interactable", "frame": 0, "id": 0}
    - {"ref": "keypoint", "frame": 0, "id": 7}
    - {"ref": "neighbour", "point": <expr>, "id": 3}
    - {"ref": "attr", "obj": <expr>, "name": "image"}
    - {"ref": "index", "list": <expr>, "index": <expr>}
    - {"op": "map_attr", "list": <expr>, "attr": "image"}
    - {"op": "filter_mask", "items": <expr>, "mask": <expr>}
    - {"op": "len", "value": <expr>}
    - {"op": "sum", "value": <expr>}
    """
    if expr is None or isinstance(expr, (str, int, float, bool)):
        return expr

    if isinstance(expr, list):
        return [_eval_expr(x, env=env, frames=frames) for x in expr]

    if isinstance(expr, dict):
        # Variable reference
        if "var" in expr:
            name = expr["var"]
            if not isinstance(name, str):
                raise ToolError("Expression var name must be string")
            if name not in env:
                raise ToolError(f"Undefined variable: {name}")
            return env[name]

        # Reference selectors
        if expr.get("ref") == "frame":
            frame_id = expr.get("id")
            if not isinstance(frame_id, int) or not (0 <= frame_id < len(frames)):
                raise ToolError(f"Invalid frame id: {frame_id}")
            return frames[frame_id]

        if expr.get("ref") == "interactable":
            frame_id = expr.get("frame")
            interactable_id = expr.get("id")
            if not isinstance(frame_id, int) or not (0 <= frame_id < len(frames)):
                raise ToolError(f"Invalid frame id: {frame_id}")
            if not isinstance(interactable_id, int) or interactable_id < 0:
                raise ToolError(f"Invalid interactable id: {interactable_id}")
            return frames[frame_id].get_interactable(interactable_id)

        if expr.get("ref") == "keypoint":
            frame_id = expr.get("frame")
            keypoint_id = expr.get("id")
            if not isinstance(frame_id, int) or not (0 <= frame_id < len(frames)):
                raise ToolError(f"Invalid frame id: {frame_id}")
            if not isinstance(keypoint_id, int) or keypoint_id < 0:
                raise ToolError(f"Invalid keypoint id: {keypoint_id}")
            return frames[frame_id].get_keypoint(keypoint_id)

        if expr.get("ref") == "neighbour":
            point_expr = expr.get("point")
            neighbour_id = expr.get("id")
            point = _eval_expr(point_expr, env=env, frames=frames)
            if not hasattr(point, "get_neighbour"):
                raise ToolError("neighbour.point must evaluate to a Point-like object with get_neighbour()")
            if not isinstance(neighbour_id, int) or neighbour_id < 0:
                raise ToolError(f"Invalid neighbour id: {neighbour_id}")
            return point.get_neighbour(neighbour_id)

        if expr.get("ref") == "attr":
            obj = _eval_expr(expr.get("obj"), env=env, frames=frames)
            name = expr.get("name")
            if not isinstance(name, str):
                raise ToolError("attr.name must be string")
            if name.startswith("__"):
                raise ToolError("Dunder attribute access is not allowed")
            return getattr(obj, name)

        if expr.get("ref") == "index":
            lst = _eval_expr(expr.get("list"), env=env, frames=frames)
            idx = _eval_expr(expr.get("index"), env=env, frames=frames)
            if not isinstance(idx, int):
                raise ToolError("index.index must evaluate to int")
            return lst[idx]

        # Expression operations
        if expr.get("op") == "map_attr":
            items = _eval_expr(expr.get("list"), env=env, frames=frames)
            attr = expr.get("attr")
            if not isinstance(attr, str) or attr.startswith("__"):
                raise ToolError("map_attr.attr must be a non-dunder string")
            return [getattr(item, attr) for item in items]

        if expr.get("op") == "filter_mask":
            items = _eval_expr(expr.get("items"), env=env, frames=frames)
            mask = _eval_expr(expr.get("mask"), env=env, frames=frames)
            if not isinstance(items, list) or not isinstance(mask, list):
                raise ToolError("filter_mask requires list items and list mask")
            if len(items) != len(mask):
                raise ToolError("filter_mask items and mask must be same length")
            out: list[Any] = []
            for item, flag in zip(items, mask):
                if not isinstance(flag, bool):
                    raise ToolError("filter_mask mask must contain booleans")
                if flag:
                    out.append(item)
            return out

        if expr.get("op") == "len":
            value = _eval_expr(expr.get("value"), env=env, frames=frames)
            return len(value)

        if expr.get("op") == "sum":
            value = _eval_expr(expr.get("value"), env=env, frames=frames)
            return sum(value)

    raise ToolError(f"Unsupported expression: {expr}")


def execute_stage3_program(
    frames: list["Frame"],
    program: Stage3Program,
    *,
    registry: ToolRegistry | None = None,
    invoker: ToolInvoker | None = None,
    op_budget: int = 2000,
) -> None:
    """
    Execute the Stage 3 restricted program.
    """
    if registry is None and invoker is None:
        raise ValueError("execute_stage3_program requires either `registry` or `invoker`")

    env: dict[str, Any] = {}

    def run_steps(steps: list[dict[str, Any]]) -> None:
        nonlocal op_budget
        for step in steps:
            op_budget -= 1
            if op_budget < 0:
                raise ToolError("Stage 3 program exceeded operation budget")

            op = step.get("op")
            if op == "call":
                tool_name = step.get("tool")
                if not isinstance(tool_name, str):
                    raise ToolError("call.tool must be string")

                args_obj = step.get("args", {})
                if not isinstance(args_obj, dict):
                    raise ToolError("call.args must be object")

                args: dict[str, Any] = {k: _eval_expr(v, env=env, frames=frames) for k, v in args_obj.items()}
                try:
                    if invoker is not None:
                        result = invoker.call_tool(tool_name, args=args)
                    else:
                        assert registry is not None  # for type checkers
                        spec = registry.get(tool_name)
                        if not spec:
                            raise ToolError(f"Tool not allowed: {tool_name}")
                        result = spec.fn(**args)
                except Exception as exc:
                    raise ToolError(f"Tool call failed: {tool_name}: {exc}") from exc

                save_as = step.get("save_as")
                if save_as is not None:
                    if not isinstance(save_as, str) or not save_as:
                        raise ToolError("call.save_as must be non-empty string")
                    env[save_as] = result

            elif op == "call_method":
                target = _eval_expr(step.get("target"), env=env, frames=frames)
                method = step.get("method")
                if not isinstance(method, str) or not method:
                    raise ToolError("call_method.method must be string")
                _ensure_allowed_method(target, method)
                fn = getattr(target, method)

                args_obj = step.get("args", {})
                if not isinstance(args_obj, dict):
                    raise ToolError("call_method.args must be object")
                args = {k: _eval_expr(v, env=env, frames=frames) for k, v in args_obj.items()}

                try:
                    result = fn(**args)
                except Exception as exc:
                    raise ToolError(f"Method call failed: {_class_name(target)}.{method}: {exc}") from exc

                save_as = step.get("save_as")
                if save_as is not None:
                    if not isinstance(save_as, str) or not save_as:
                        raise ToolError("call_method.save_as must be non-empty string")
                    env[save_as] = result

            elif op == "assign":
                name = step.get("var")
                if not isinstance(name, str) or not name:
                    raise ToolError("assign.var must be non-empty string")
                env[name] = _eval_expr(step.get("value"), env=env, frames=frames)

            elif op == "foreach":
                var = step.get("var")
                if not isinstance(var, str) or not var:
                    raise ToolError("foreach.var must be non-empty string")
                iterable = _eval_expr(step.get("in"), env=env, frames=frames)
                if not isinstance(iterable, list):
                    raise ToolError("foreach.in must evaluate to a list")
                body = step.get("do", [])
                if not isinstance(body, list):
                    raise ToolError("foreach.do must be a list of steps")
                try:
                    for item in iterable:
                        env[var] = item
                        run_steps(body)
                except _Break:
                    pass

            elif op == "if":
                cond = _eval_expr(step.get("cond"), env=env, frames=frames)
                then_steps = step.get("then", [])
                else_steps = step.get("else", [])
                if not isinstance(then_steps, list) or not isinstance(else_steps, list):
                    raise ToolError("if.then/if.else must be list of steps")
                if cond:
                    run_steps(then_steps)
                else:
                    run_steps(else_steps)

            elif op == "break":
                raise _Break()

            else:
                raise ToolError(f"Unknown step op: {op!r}")

    run_steps(program.steps)
