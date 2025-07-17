# Action handles for all interactable frames and elements.
# Provides VLM agents with the ability to interact and execute actions (i.e., enhance executive function).
from __future__ import annotations
import io
import time
import itertools
from copy import deepcopy
from typing import Union, Literal, List

import PIL.Image
from PIL import ImageChops
from dotenv import load_dotenv
from playwright.sync_api import Page

from halligan.utils.toolkit import Toolkit
from halligan.utils.layout import Frame, Element, Point
from halligan.utils.vision_tools import match


load_dotenv()

page: Page | None = None


def set_page(p: Page):
    global page
    page = p


def screenshot(region: list[float] = None) -> PIL.Image.Image:
    if region:
        region = {
            "x": region[0], "y": region[1],
            "width": region[2], "height": region[3]
        }
    image_bytes = page.screenshot(clip=region)
    return PIL.Image.open(io.BytesIO(image_bytes)).convert("RGB")


class Choice:
    def __init__(self, image: PIL.Image.Image) -> None:
        self._image = image

    @property
    def image(self) -> PIL.Image.Image:
        return self._image
    
    def release(self) -> None:
        """
        (For click_and_hold) Release from holding. 
        """
        page.mouse.up()


class SelectChoice:
    def __init__(self, index: int, image: PIL.Image.Image, next: Element) -> None:
        self._image = image
        self._index = index
        self._next = next

    @property
    def image(self) -> PIL.Image.Image:
        return self._image

    def select(self) -> None:
        """
        (For get_all_choices) Select this choice.
        """
        x = self._next.x + self._next.w // 2
        y = self._next.y + self._next.h // 2
        for _ in range(self._index):
            page.mouse.click(x, y)


class SlideChoice:
    def __init__(
        self, 
        axis: Literal["x", "y"],
        image: PIL.Image.Image, 
        current_x: int,
        current_y: int, 
        observe: Frame,
        track_bounds: tuple[int, int]
    ) -> None:
        self._axis = axis
        self._image = image
        self._current_x = current_x
        self._current_y = current_y
        self._observe = observe
        self._track_bounds = track_bounds
        
    @property
    def image(self) -> PIL.Image.Image:
        """
        Image capturing the observation.
        """
        return self._image

    def refine(self) -> list[SlideChoice]:
        """
        Reduce the search space for further analysis by narrowing down to a subset of choices around this option.
        Note: The list is not ordered. The first choice is not necessarily the best choice.
        All returned options should be considered equally before release().
        """
        refine_range, step = 20, 4
        refine_pos = self._current_x if self._axis == "x" else self._current_y
        min_bound = max(self._track_bounds[0], refine_pos - refine_range)
        max_bound = min(self._track_bounds[1], refine_pos + refine_range)

        choices = []
        for pos in range(min_bound, max_bound, step):
            if self._axis == "x":
                page.mouse.move(x=pos, y=self._current_y)
                image = screenshot(self._observe.region)
                choice = SlideChoice(self._axis, image, pos, self._current_y, self._observe, (min_bound, max_bound))
            else:
                page.mouse.move(x=self._current_x, y=pos)
                image = screenshot(self._observe.region)
                choice = SlideChoice(self._axis, image, self._current_x, pos, self._observe, (min_bound, max_bound))            

            choices.append(choice)
        
        return choices
    
    def release(self) -> None:
        """
        Confirm this as the final choice and release slider.
        """
        page.mouse.move(self._current_x, self._current_y)
        page.mouse.up()
    

class SwapChoice:
    def __init__(
        self, 
        grid: list[list[Element]], 
        image: PIL.Image.Image,
        start: tuple[int, int],
        end: tuple[int, int]
    ) -> None:
        self._grid = grid
        self._image = image
        self._start = start
        self._end = end
        
    @property
    def preview(self) -> PIL.Image.Image:
        """
        A preview image of the grid after swap.
        """
        return self._image
    
    @property
    def grid(self) -> list[list[Element]]:
        """
        A 2D list previewing the grid of elements after the swap.
        For solutions that need to compare for elements (i.e., visual identity, position) in the grid.
        For example: compare() identical elements in a row or column.
        """
        return self._grid
        
    def swap(self) -> None:
        """
        Executes the swap previewed in this choice.
        """
        x1, y1 = self._start
        x2, y2 = self._end

        # Attempt 1: click start and end 
        page.mouse.click(x1, y1)
        page.mouse.click(x2, y2)

        # Attempt 2: drag start to end
        page.mouse.move(x1, y1)
        page.mouse.down()
        page.mouse.move(x2, y2)
        page.mouse.up()


class DragChoice:
    def __init__(self, image: PIL.Image.Image, start: tuple, end: tuple) -> None:
        self._image = image
        self._start = start
        self._end = end
    
    @property
    def preview(self) -> PIL.Image.Image:
        """
        A preview of the drag-and-drop results.
        """
        return self._image
    
    def drop(self) -> None:
        """
        Confirm this as the final choice and drop here.
        """
        x1, y1 = self._start
        x2, y2 = self._end
        page.mouse.move(x1, y1)
        page.mouse.down()
        page.mouse.move(x2, y2)
        page.mouse.up()
        

def click(target: Union[Frame, Element]) -> None:
    """
    Click a UI button.
    """
    x, y = target.center
    page.mouse.click(x, y)


def click_and_hold(target: Union[Frame, Element], observe: Frame):
    """
    Hold until release, returns observed state while holding.
    This action happens in real-time, do not batch process.
    Yields:
        choice (Choice): The latest frame observation.
    Example:
        for choice in click_and_hold(...):
            if ask([choice.image], "ready to release?"): break
    """
    x, y = target.center
    region = observe.region
    page.mouse.down(x, y)
    start_time = time.time()
    timeout = 10

    while True:
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout: break

        image = screenshot(region)
        yield Choice(image)


def get_all_choices(prev_arrow: Element, next_arrow: Element, observe: Frame) -> list[SelectChoice]:
    """
    Cycle through all choices by clicking arrow buttons.
    Returns all cycled choices from frame.
    """
    def same_as(diff: PIL.Image.Image) -> bool:
        if not diff_with_first.getbbox(): return True
        diff = diff.convert("L")
        total_diff = sum(diff.getdata())
        max_diff = diff.size[0] * diff.size[1] * 255
        diff_ratio = total_diff / max_diff
        return diff_ratio < 0.01

    index = 0
    region = observe.region
    choices = [SelectChoice(index, screenshot(region), next_arrow)]
    next_x, next_y = next_arrow.center
    prev_x, prev_y = prev_arrow.center

    while True:
        page.mouse.click(next_x, next_y)
        image = screenshot(region)
        diff_with_first = ImageChops.difference(image, choices[0].image)
        diff_with_prev = ImageChops.difference(image, choices[-1].image)

        # Same as first means we have gone through a full cycle.
        if same_as(diff_with_first): break

        # Same as prev means it has reached the end but can't cycle back, manually do so.
        if same_as(diff_with_prev):
            for _ in range(len(choices) - 1): 
                page.mouse.click(prev_x, prev_y)
            break

        index += 1
        choices.append(SelectChoice(index, image, next_arrow))

    return choices


def drag(start: Element, end: Point) -> list[DragChoice]:
    """
    Drag element from start to end point.

    Returns:
        drag_choices (list[DragChoice]): make minor adjustments at the endpoint.
    """
    import cv2
    import numpy as np
    def get_mask(image: PIL.Image.Image) -> np.ndarray:
        image = np.array(image)
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        #mask = cv2.bitwise_not(mask) 
        mask = PIL.Image.fromarray(mask).convert('L')
        return mask

    x2, y2 = end.center
    choices = []
    step = 10
    # Create 3 x 3 choices centered at (x, y) with step size 10px
    for i in range(-1, 2):
        for j in range(-1, 2):
            cx = x2 + i * step
            cy = y2 + j * step
            margin = 20
            region = [
                cx - start.w // 2 - margin,
                cy - start.h // 2 - margin,
                start.w + margin * 2,
                start.h + margin * 2
            ]
            mask = get_mask(start.image)
            image = screenshot(region)
            image.paste(start.image, box=(margin, margin), mask=mask)
            choices.append(DragChoice(image, start.center, end=(cx, cy)))

    return choices


def draw(path: list[Point]) -> None:
    """
    Draw a path following a list of points.
    """
    if not path: return

    x, y = path[0]
    page.mouse.move(x, y)
    page.mouse.down()

    for point in path: 
        page.mouse.move(point.x, point.y)

    x, y = path[-1]
    page.mouse.move(x, y)
    page.mouse.up()


def enter(field: Union[Frame, Element], text: str) -> None:
    """
    Click on an input field and enter text.
    """
    x, y = field.center
    page.mouse.click(x, y)
    page.keyboard.type(text)


def point(to: Point) -> None:
    """
    Click on a point on a frame.
    """
    x, y = to.center
    page.mouse.click(x, y)


def select(choice: Union[Frame, Element]) -> None:
    """
    Select a choice.
    """
    x, y = choice.center
    page.mouse.click(x, y)


def slide_x(handle: Element, direction: Literal['left', 'right'], observe_frame: Frame) -> list[SlideChoice]:
    """
    Drag and move slider handle left/right while observing changes in a frame.

    Returns:
        observation (list[Choice]): observation over frame while sliding.
    """
    track_bounds = (handle.parent.x, handle.parent.x + handle.parent.w)
    step_size = handle.w // 2   
    step = -step_size if direction == "left" else step_size

    choices = []
    current_x = handle.x + handle.w // 2
    current_y = handle.y + handle.h // 2
    page.mouse.move(current_x, current_y)
    page.mouse.down()

    while track_bounds[0] < current_x + handle.w < track_bounds[1]:
        current_x += step
        page.mouse.move(current_x, current_y)
        image = screenshot(observe_frame.region)
        refine_range = [track_bounds[0] + step, track_bounds[1] - step]
        choice = SlideChoice("x", image, current_x, current_y, observe_frame, refine_range)
        choices.append(choice)

    return choices


def slide_y(handle: Element, direction: Literal['up', 'down'], observe_frame: Frame) -> list[SlideChoice]:
    """
    Drag and move slider handle up/down while observing changes in a frame.

    Returns:
        observation (list[Choice]): observation over frame while sliding.
    """
    track_bounds = (handle.parent.y, handle.parent.y + handle.parent.h)
    step_size = handle.h // 2   
    step = -step_size if direction.lower() == "down" else step_size

    choices = []
    current_x = handle.x + handle.w // 2
    current_y = handle.y + handle.h // 2
    page.mouse.move(current_x, current_y)
    page.mouse.down()

    while track_bounds[0] < current_y + step < track_bounds[1]:
        page.mouse.move(current_x, current_y)
        image = screenshot(observe_frame.region)
        choice = SlideChoice("y", image, current_x, current_y, observe_frame, track_bounds)
        choices.append(choice)
        current_y += step

    return choices


def explore(grid: Frame) -> list[SwapChoice]:
    """
    Get all possible ways to swap elements in the grid.

    Returns:
        choices (list[Choice]): all possible swaps.
    """
    # Step 1: build the grid of elements
    elements = sorted(grid.interactables, key=lambda e: e.y)
    rows: list[list[Element]] = []
    current_row_y = None
    for element in elements:
        # Start a new row
        if current_row_y is None or element.y != current_row_y:
            rows.append([])
            current_row_y = element.y

        rows[-1].append(element)

    element_grid: list[list[Element]] = [sorted(row, key=lambda el: el.x) for row in rows]

    # Step 2: get all possible swaps ordered by swap distance
    rows, cols = len(rows), len(rows[-1])
    choices_by_distance = {d: [] for d in range(1, rows + cols)}
    all_cells = list(itertools.product(range(rows), range(cols)))

    for (r1, c1), (r2, c2) in itertools.combinations(all_cells, 2):
        if match(element_grid[r1][c1], element_grid[r2][c2]): continue

        manhattan_distance = abs(r1 - r2) + abs(c1 - c2)
        swapped_grid = deepcopy(element_grid)

        # Update grid image
        image = grid.image.copy()
        image.paste(swapped_grid[r1][c1].image, (swapped_grid[r2][c2].x - grid.x, swapped_grid[r2][c2].y - grid.y))
        image.paste(swapped_grid[r2][c2].image, (swapped_grid[r1][c1].x - grid.x, swapped_grid[r1][c1].y - grid.y))

        # Swap elements
        swapped_grid[r1][c1].image, swapped_grid[r2][c2].image = swapped_grid[r2][c2].image, swapped_grid[r1][c1].image
        swap_from = (swapped_grid[r1][c1].x + swapped_grid[r1][c1].w // 2, swapped_grid[r1][c1].y + swapped_grid[r1][c1].h // 2)
        swap_to = (swapped_grid[r2][c2].x + swapped_grid[r2][c2].w // 2, swapped_grid[r2][c2].y + swapped_grid[r2][c2].h // 2)

        choice = SwapChoice(swapped_grid, image, swap_from, swap_to)
        choices_by_distance[manhattan_distance].append(choice)
        
    return [choice for choices in choices_by_distance.values() for choice in choices]


dependencies = {**globals(), "__builtins__": __builtins__, "List": List}

action_toolkits: dict[str, Toolkit] = {
    "DRAGGABLE": [drag, DragChoice.preview, DragChoice.drop],
    "SWAPPABLE": [explore, SwapChoice.grid, SwapChoice.preview, SwapChoice.swap],
    "SLIDEABLE_X": [slide_x, SlideChoice.image, SlideChoice.refine, SlideChoice.release],
    "SLIDEABLE_Y": [slide_y, SlideChoice.image, SlideChoice.refine, SlideChoice.release],
    "CLICKABLE": [click, get_all_choices, SelectChoice.image, SelectChoice.select],
    "POINTABLE": [point],
    "DRAWABLE": [draw],
    "INPUTTABLE": [enter],
    "SELECTABLE": [select],
    "NEXT": [click]
}

for action, tools in action_toolkits.items():
    action_toolkits[action] = Toolkit(tools=tools, dependencies=dependencies)