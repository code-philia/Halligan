from halligan.utils.vision_tools import ask, mark
from halligan.utils.action_tools import select


def stage1(frames):
    return


def stage2(frames):
    # Frame 0 is the instruction frame, so it is non-interactable
    # Frame 1 contains the squares with objects, which are interactable

    # Split Frame 1 into 6 selectable subframes (2 rows, 3 columns)
    subframes = frames[1].split(rows=2, columns=3)

    # Set each subframe as SELECTABLE
    for subframe in subframes:
        subframe.set_frame_as(interactable="SELECTABLE")


def stage3(frames):
    # Mark objects in each frame
    marked_images = mark([frame.image for frame in frames[1:]], "object")
    
    # Ask which frame contains two identical objects
    identical_objects = ask(marked_images, "Does this image contain two identical objects?", answer_type="bool")
    
    # Select the frame with two identical objects
    for i, identical in enumerate(identical_objects):
        if identical:
            select(frames[i + 1])
            break