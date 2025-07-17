from halligan.utils.action_tools import select
from halligan.utils.vision_tools import mark, ask


def stage1(frames):
    return


def stage2(frames):
    # Frame 0 is the instruction frame, so it is non-interactable
    # Frame 1 contains the dice pairs, which are interactable

    # Split Frame 1 into subframes for each pair of dice
    subframes = frames[1].split(rows=2, columns=3)

    # Set each subframe as SELECTABLE since we need to click on the correct pair
    for subframe in subframes:
        subframe.set_frame_as('SELECTABLE')


def stage3(frames):
    # Extract images from frames 1 to 6
    images = [frame.image for frame in frames[1:7]]

    # Mark the icons on the dice
    marked_images = mark(images, "icon")

    # Ask which pair of dice have the same icon facing up
    same_icon_pair = ask(marked_images, "Which pair of dice have the same icon facing up?", answer_type="int")

    # Select the frame with the matching pair
    select(frames[same_icon_pair[0] + 1])