from enum import Enum


class Stage(Enum):
    OBJECTIVE_IDENTIFICATION: int = 1
    STRUCTURE_ABSTRACTION: int = 2
    SOLUTION_COMPOSITION: int = 3


class Interactable(Enum):
    def __new__(cls, name: str, description: str):
        obj = object.__new__(cls)
        obj._name = name
        obj._description = description
        return obj

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description


class InteractableElement(Interactable):
    DRAGGABLE = ("DRAGGABLE", "Can be freely moved anywhere")
    SWAPPABLE = ("SWAPPABLE", "Can manually exchange places with another SWAPPABLE")
    SLIDEABLE_X = ("SLIDEABLE_X", "Can be dragged along a horizontal track")
    SLIDEABLE_Y = ("SLIDEABLE_Y", "Can be dragged along a vertical track")
    INPUTTABLE = ("INPUTTABLE", "You can type a text answer in this input box as an answer")
    CLICKABLE = ("CLICKABLE", "UI button that can be clicked to transition a frame or cycle through choices")
    NEXT = ("NEXT", "UI button that can be clicked to submit/skip the task")


class InteractableFrame(Interactable):
    POINTABLE = ("POINTABLE", "You can point to specific thing(s) in a 2D area as an answer")
    DRAWABLE = ("DRAWABLE", "You can draw trajectories from A to B on a frame as an answer")
    INPUTTABLE = ("INPUTTABLE", "You can type a text answer in this input box as an answer")
    SELECTABLE = ("SELECTABLE", "You can click to toggle this frame as an answer choice")
    NEXT = ("NEXT", "You can click this frame to submit/skip the task")