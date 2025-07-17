from halligan.utils.action_tools import explore
from halligan.utils.vision_tools import match


def stage2(frames):
    # Frame 0 is non-interactable because it provides instructions for Frame 1
    frame_0 = frames[0]
    
    # Frame 1 contains the grid of emoji faces
    frame_1 = frames[1]
    
    # Convert Frame 1 into a grid of swappable elements
    elements_grid = frame_1.grid(tiles=9)
    
    # Mark each element in the grid as SWAPPABLE
    for row in elements_grid:
        for element in row:
            element.set_element_as(interactable="SWAPPABLE")


def stage3(frames):
    # Explore all possible swaps in the grid
    choices = explore(frames[1])
    
    # Iterate over each swap choice
    for choice in choices:
        grid = choice.grid
        
        # Check each row for three identical elements
        for row in grid:
            if match(row[0], row[1]) and match(row[1], row[2]):
                choice.swap()
                return
        
        # Check each column for three identical elements
        for col in zip(*grid):
            if match(col[0], col[1]) and match(col[1], col[2]):
                choice.swap()
                return