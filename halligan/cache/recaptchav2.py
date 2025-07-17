from halligan.utils.action_tools import select, click
from halligan.utils.vision_tools import ask, mark


def stage1(frames):
    return


def stage2(frames):
    # Frame 0: A blank screen with a 'SKIP' button
    frame_0 = frames[0]
    skip_button = frame_0.get_element(position='down', details='blue button with text SKIP')
    skip_button.set_element_as(interactable='NEXT')

    # Frame 1: A 3x3 grid of images
    frame_1 = frames[1]
    grid_elements = frame_1.grid(tiles=9)
    for row in grid_elements:
        for element in row:
            element.set_element_as(interactable='SELECTABLE')


def stage3(frames):
    # Frame 2 provides the instruction to select images with bridges in Frame 1
    instruction_frame = frames[2] if len(frames) == 3 else frames[0]
    image_frame = frames[1]

    target_object = ask([instruction_frame.image], "What is the target object?", "str")
    target_object = "".join(target_object)

    # Mark images in Frame 1 to identify bridges
    marked_images = mark([image_frame.get_interactable(i).image for i in range(9)], target_object)

    # Ask which images contain bridges
    bridge_answers = ask(marked_images, f"Does this image contain a {target_object}?", answer_type="bool")

    # Select images that contain bridges
    for i, has_bridge in enumerate(bridge_answers):
        if has_bridge:
            select(image_frame.get_interactable(i))

    # Click 'NEXT' to proceed
    next_button = frames[0].get_interactable(0)
    click(next_button)