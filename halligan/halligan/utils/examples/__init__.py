import os
from collections import defaultdict

from halligan.utils.constants import InteractableFrame, InteractableElement


def _get_example(interactable: str) -> str:
    """Get an in-context example.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_path, interactable)
    return open(path).read()


_EXAMPLES = defaultdict(lambda: _get_example("generic.txt"), {
    InteractableFrame.DRAWABLE.name      : _get_example("drawable.txt"),
    InteractableFrame.POINTABLE.name     : _get_example("pointable.txt"),
    InteractableFrame.SELECTABLE.name    : _get_example("selectable.txt"),
    InteractableElement.CLICKABLE.name   : _get_example("clickable.txt"),
    InteractableElement.DRAGGABLE.name   : _get_example("draggable.txt"),
    InteractableElement.SLIDEABLE_X.name : _get_example("slideable.txt"),
    InteractableElement.SLIDEABLE_Y.name : _get_example("slideable.txt"),
    InteractableElement.SWAPPABLE.name   : _get_example("swappable.txt"),
    InteractableElement.INPUTTABLE.name  : _get_example("inputtable.txt")
})


def get(interactable: str) -> str:
    """
    Get in-context learning examples based on interactable type.
    """
    return _EXAMPLES[interactable]