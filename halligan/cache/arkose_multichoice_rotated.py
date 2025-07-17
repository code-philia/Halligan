from halligan.utils.vision_tools import ask
from halligan.utils.action_tools import select


def stage1(frames):
    return


def stage2(frames):
    # Frame 0 provides instructions, so it is not interactable
    # Frame 1 contains the grid of images, which are selectable

    # Split Frame 1 into a grid of selectable subframes
    subframes = frames[1].split(rows=2, columns=3)
    
    # Mark each subframe as SELECTABLE
    for subframe in subframes:
        subframe.set_frame_as(interactable="SELECTABLE")

        
def stage3(frames):
    # Extract images from frames 1 to 6
    images = [frame.image for frame in frames[1:7]]
    
    # Ask which image is the correct way up
    correct_orientation = ask(images, "Which image is the correct way up?", answer_type="int")
    
    # Select the frame with the correct orientation
    select(frames[correct_orientation[0] + 1])