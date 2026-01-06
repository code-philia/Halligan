from __future__ import annotations

import pytest

from halligan.runtime.errors import ToolError, ValidationError
from halligan.runtime.executor import apply_stage2_plan, execute_stage3_program
from halligan.runtime.registry import ToolRegistry
from halligan.runtime.schemas import Stage2Action, Stage2Plan, Stage3Program


class DummyElement:
    def __init__(self, parent: "DummyFrame") -> None:
        self.parent = parent
        self.interactable: str | None = None

    def set_element_as(self, interactable: str) -> None:
        self.interactable = interactable
        self.parent.interactables.append(self)


class DummyFrame:
    def __init__(self) -> None:
        self.interactable: str | None = None
        self.interactables: list[DummyElement] = []
        self.subframes: list["DummyFrame"] = []

    def set_frame_as(self, interactable: str) -> None:
        self.interactable = interactable

    def split(self, *, rows: int, columns: int) -> list["DummyFrame"]:
        self.subframes = [DummyFrame() for _ in range(rows * columns)]
        return self.subframes

    def grid(self, *, tiles: int) -> list[list[DummyElement]]:
        # Minimal 1-row grid is enough for executor validation.
        return [[DummyElement(self) for _ in range(tiles)]]

    def get_element(self, *, position: str, details: str) -> DummyElement:
        return DummyElement(self)

    def get_interactable(self, id: int):
        return self.interactables[id] if self.interactables else self


def test_stage2_plan_enforces_single_interactable_type():
    frames = [DummyFrame()]

    plan = Stage2Plan(
        actions=[
            Stage2Action(type="split_frame", payload={"frame": 0, "rows": 2, "columns": 2, "mark_as": "SELECTABLE"}),
            # Introduce a second non-NEXT interactable type -> should fail post-validation
            Stage2Action(type="grid_frame", payload={"frame": 0, "tiles": 4, "mark_as": "SWAPPABLE"}),
        ]
    )

    with pytest.raises(ValidationError):
        apply_stage2_plan(frames, plan)


def test_stage3_executor_calls_registered_tools():
    reg = ToolRegistry()

    def echo(*, value):
        return value

    reg.register("echo", echo)

    program = Stage3Program(
        steps=[
            {"op": "call", "tool": "echo", "args": {"value": 123}, "save_as": "out"},
            {"op": "call", "tool": "echo", "args": {"value": {"var": "out"}}, "save_as": "out2"},
        ]
    )

    frames = [DummyFrame()]
    execute_stage3_program(frames, program, registry=reg)


def test_stage3_executor_blocks_unknown_tool():
    reg = ToolRegistry()
    program = Stage3Program(steps=[{"op": "call", "tool": "nope", "args": {}}])
    frames = [DummyFrame()]
    with pytest.raises(ToolError):
        execute_stage3_program(frames, program, registry=reg)


def test_stage3_executor_enforces_op_budget():
    reg = ToolRegistry()

    def echo(*, value):
        return value

    reg.register("echo", echo)

    program = Stage3Program(
        steps=[
            {"op": "assign", "var": "items", "value": [1, 2, 3, 4, 5]},
            {
                "op": "foreach",
                "var": "x",
                "in": {"var": "items"},
                "do": [{"op": "call", "tool": "echo", "args": {"value": {"var": "x"}}}],
            },
        ]
    )

    frames = [DummyFrame()]
    with pytest.raises(ToolError):
        execute_stage3_program(frames, program, registry=reg, op_budget=3)

    execute_stage3_program(frames, program, registry=reg, op_budget=100)
