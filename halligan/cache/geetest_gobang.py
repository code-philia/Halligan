from halligan.utils.vision_tools import match
from halligan.utils.action_tools import explore


def stage1(frames):
    return


def stage2(frames):
    # Frame 0 provides instructions, so it is non-interactable
    # Frame 1 contains the grid of colored circles

    # Access Frame 1
    frame1 = frames[1]

    # Convert Frame 1 into a grid of swappable elements
    grid_elements = frame1.grid(tiles=25)  # Assuming a 5x5 grid

    # Set each element in the grid as SWAPPABLE
    for row in grid_elements:
        for element in row:
            element.set_element_as(interactable="SWAPPABLE")


def stage3(frames):
    # Explore all possible swaps in Frame 1
    choices = explore(frames[1])

    # Iterate over each swap choice
    for choice in choices:
        grid = choice.grid
        
        # Check each row for five identical elements
        for row in grid:
            if all(match(row[0], element) for element in row):
                choice.swap()
                return

        # Check each column for five identical elements
        for col in zip(*grid):
            if all(match(col[0], element) for element in col):
                choice.swap()
                return

        # Check diagonals for five identical elements
        if all(match(grid[i][i], grid[0][0]) for i in range(len(grid))):
            choice.swap()
            return
        if all(match(grid[i][len(grid)-i-1], grid[0][len(grid)-1]) for i in range(len(grid))):
            choice.swap()
            return

    # If no solution is found, rank the choices to find the best configuration
    # ranked_choices = rank([choice.preview for choice in choices], "Which image is complete?")
    # best_choice = next(choice for choice in choices if choice.preview == ranked_choices[0])
    # best_choice.swap()