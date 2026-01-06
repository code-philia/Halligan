from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from halligan.runtime.errors import ValidationError
from halligan.utils.constants import InteractableElement, InteractableFrame

# -----------------------------
# Helpers
# -----------------------------


def _require_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"Expected object at {path}, got {type(value).__name__}")
    return value


def _require_list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"Expected array at {path}, got {type(value).__name__}")
    return value


def _require_str(value: Any, path: str) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"Expected string at {path}, got {type(value).__name__}")
    return value


def _require_int(value: Any, path: str) -> int:
    if not isinstance(value, int):
        raise ValidationError(f"Expected integer at {path}, got {type(value).__name__}")
    return value


def _require_bool(value: Any, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValidationError(f"Expected boolean at {path}, got {type(value).__name__}")
    return value


def _require_one_of(value: str, allowed: set[str], path: str) -> str:
    if value not in allowed:
        raise ValidationError(f"Invalid value at {path}: {value!r}. Allowed: {sorted(allowed)}")
    return value


def _require_optional_int(value: Any, path: str) -> int | None:
    if value is None:
        return None
    return _require_int(value, path)


_FRAME_INTERACTABLES: set[str] = {it.name for it in InteractableFrame}
_ELEMENT_INTERACTABLES: set[str] = {it.name for it in InteractableElement}


# -----------------------------
# Stage 1 schema
# -----------------------------


@dataclass(frozen=True)
class Stage1Relation:
    src: int
    dst: int | None
    relationship: str


@dataclass(frozen=True)
class Stage1Result:
    descriptions: list[str]
    relations: list[Stage1Relation]
    objective: str


def validate_stage1(data: Any, *, frames: int) -> Stage1Result:
    obj = _require_dict(data, "$")

    descriptions = _require_list(obj.get("descriptions"), "$.descriptions")
    if len(descriptions) != frames:
        raise ValidationError(f"$.descriptions length mismatch: expected {frames}, got {len(descriptions)}")
    desc_out: list[str] = []
    for i, d in enumerate(descriptions):
        desc_out.append(_require_str(d, f"$.descriptions[{i}]").strip())

    relations_raw = _require_list(obj.get("relations", []), "$.relations")
    rel_out: list[Stage1Relation] = []
    for i, rel in enumerate(relations_raw):
        rel_obj = _require_dict(rel, f"$.relations[{i}]")
        src = _require_int(rel_obj.get("from"), f"$.relations[{i}].from")
        dst = _require_optional_int(rel_obj.get("to"), f"$.relations[{i}].to")
        relationship = _require_str(rel_obj.get("relationship", ""), f"$.relations[{i}].relationship").strip()

        if not (0 <= src < frames):
            raise ValidationError(f"$.relations[{i}].from out of range: {src}")
        if dst is not None and not (0 <= dst < frames):
            raise ValidationError(f"$.relations[{i}].to out of range: {dst}")

        rel_out.append(Stage1Relation(src=src, dst=dst, relationship=relationship))

    objective = _require_str(obj.get("objective"), "$.objective").strip()
    if not objective:
        raise ValidationError("$.objective must be non-empty")

    return Stage1Result(descriptions=desc_out, relations=rel_out, objective=objective)


# -----------------------------
# Stage 2 schema
# -----------------------------


Stage2ActionType = Literal["set_frame", "split_frame", "grid_frame", "get_element"]


@dataclass(frozen=True)
class Stage2Action:
    type: Stage2ActionType
    payload: dict[str, Any]


@dataclass(frozen=True)
class Stage2Plan:
    actions: list[Stage2Action]


_POSITIONS = {"up", "down", "left", "right", "all"}


def validate_stage2(data: Any, *, frames: int) -> Stage2Plan:
    obj = _require_dict(data, "$")
    actions_raw = _require_list(obj.get("actions"), "$.actions")

    actions: list[Stage2Action] = []
    for i, item in enumerate(actions_raw):
        action_obj = _require_dict(item, f"$.actions[{i}]")
        action_type = _require_str(action_obj.get("type"), f"$.actions[{i}].type")
        action_type = _require_one_of(action_type, {"set_frame", "split_frame", "grid_frame", "get_element"}, f"$.actions[{i}].type")  # type: ignore[assignment]

        frame_id = _require_int(action_obj.get("frame"), f"$.actions[{i}].frame")
        if not (0 <= frame_id < frames):
            raise ValidationError(f"$.actions[{i}].frame out of range: {frame_id}")

        if action_type == "set_frame":
            interactable = _require_str(action_obj.get("interactable"), f"$.actions[{i}].interactable")
            _require_one_of(interactable, _FRAME_INTERACTABLES, f"$.actions[{i}].interactable")
            actions.append(Stage2Action(type="set_frame", payload={"frame": frame_id, "interactable": interactable}))

        elif action_type == "split_frame":
            rows = _require_int(action_obj.get("rows"), f"$.actions[{i}].rows")
            columns = _require_int(action_obj.get("columns"), f"$.actions[{i}].columns")
            mark_as = _require_str(action_obj.get("mark_as"), f"$.actions[{i}].mark_as")
            _require_one_of(mark_as, _FRAME_INTERACTABLES, f"$.actions[{i}].mark_as")
            if rows <= 0 or columns <= 0:
                raise ValidationError(f"$.actions[{i}] rows/columns must be positive")
            actions.append(
                Stage2Action(
                    type="split_frame",
                    payload={"frame": frame_id, "rows": rows, "columns": columns, "mark_as": mark_as},
                )
            )

        elif action_type == "grid_frame":
            tiles = _require_int(action_obj.get("tiles"), f"$.actions[{i}].tiles")
            mark_as = _require_str(action_obj.get("mark_as"), f"$.actions[{i}].mark_as")
            _require_one_of(mark_as, _ELEMENT_INTERACTABLES, f"$.actions[{i}].mark_as")
            if tiles <= 0:
                raise ValidationError(f"$.actions[{i}].tiles must be positive")
            actions.append(
                Stage2Action(type="grid_frame", payload={"frame": frame_id, "tiles": tiles, "mark_as": mark_as})
            )

        elif action_type == "get_element":
            position = _require_str(action_obj.get("position"), f"$.actions[{i}].position")
            _require_one_of(position, _POSITIONS, f"$.actions[{i}].position")
            details = _require_str(action_obj.get("details"), f"$.actions[{i}].details").strip()
            if not details:
                raise ValidationError(f"$.actions[{i}].details must be non-empty")
            mark_as = _require_str(action_obj.get("mark_as"), f"$.actions[{i}].mark_as")
            _require_one_of(mark_as, _ELEMENT_INTERACTABLES, f"$.actions[{i}].mark_as")
            actions.append(
                Stage2Action(
                    type="get_element",
                    payload={"frame": frame_id, "position": position, "details": details, "mark_as": mark_as},
                )
            )

        else:
            raise ValidationError(f"Unknown action type at $.actions[{i}].type: {action_type}")

    return Stage2Plan(actions=actions)


# -----------------------------
# Stage 3 schema (restricted DSL)
# -----------------------------


Stage3StmtType = Literal["call", "assign", "if", "foreach", "break"]


@dataclass(frozen=True)
class Stage3Program:
    """
    A restricted, JSON-based program for safe execution.

    This is intentionally minimal and only supports a small set of statements.
    """

    steps: list[dict[str, Any]]


def validate_stage3(data: Any) -> Stage3Program:
    obj = _require_dict(data, "$")
    steps = _require_list(obj.get("steps"), "$.steps")
    # We keep validation light here and enforce the rest at execution time,
    # because allowed tools depend on the interactable types discovered in Stage 2.
    for i, step in enumerate(steps):
        _require_dict(step, f"$.steps[{i}]")
        _require_str(step.get("op"), f"$.steps[{i}].op")
    return Stage3Program(steps=steps)  # type: ignore[arg-type]
