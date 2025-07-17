from halligan.utils.vision_tools import compare
from halligan.utils.action_tools import click, select


def stage1(frames):
    return


def stage2(frames):
    for frame in frames:
        if frame == frames[0]:  # Frame 0
            # Get the 'Skip' button and mark it as NEXT
            skip_button = frame.get_element(position="down", details="gray rectangular button with 'Skip'")
            skip_button.set_element_as(interactable="NEXT")
        
        elif frame == frames[1]:  # Frame 1
            # Mark the frame as POINTABLE for selecting matching entities
            frame.set_frame_as(interactable="POINTABLE")
        
        elif frame in frames[2:]:  # Frames 2-10
            # Mark each frame as SELECTABLE for matching entities
            frame.set_frame_as(interactable="SELECTABLE")


def stage3(frames):
    # Step 1: Extract the pattern image from Frame 1
    pattern_image = frames[1].image

    # Step 2: Compare the pattern with the options in Frames 2-10
    option_images = [frame.image for frame in frames[2:]]
    matches = compare(option_images, "Does this match the pattern?", reference=pattern_image)

    # Step 3: Select matching frames or click 'Skip' if no matches exist
    if any(matches):
        for i, match in enumerate(matches):
            if match:
                select(frames[i + 2])  # Select the matching frame

    skip_button_frame_0 = frames[0].get_interactable(0)
    click(skip_button_frame_0)