from halligan.utils.action_tools import select
from halligan.utils.vision_tools import ask


def stage1(frames):
    return


def stage2(frames):
    # Frame 0 is a prompt and not interactable
    # Frame 1 contains the grid of images
    frame1 = frames[1]
    
    # Split Frame 1 into a grid of 6 images
    subframes = frame1.split(rows=2, columns=3)
    
    # Mark each subframe as SELECTABLE since we need to click one of them
    for subframe in subframes:
        subframe.set_frame_as(interactable="SELECTABLE")


def stage3(frames):
    # Extract images from frames 1 to 6
    images = [frame.image for frame in frames[1:7]]
    
    # Ask which image contains a spiral galaxy pattern
    spiral_galaxy_indices = ask(images, "Which image contains a spiral galaxy pattern?", answer_type="int")
    
    # Select the frame with the spiral galaxy
    select(frames[spiral_galaxy_indices[0] + 1])