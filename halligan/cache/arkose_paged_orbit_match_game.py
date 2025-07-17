from halligan.utils.vision_tools import mark, compare, ask
from halligan.utils.action_tools import get_all_choices, click


def stage1(frames):
    return


def stage2(frames):
    # Frame 0: Instruction frame
    frame_0 = frames[0]
    frame_0.set_frame_as("POINTABLE")  # Instructions are pointable for reference.

    # Frame 1: Circular orbit map with icons and arrow buttons
    frame_1 = frames[1]
    left_arrow = frame_1.get_element("left", "white circular button with left arrow")
    right_arrow = frame_1.get_element("right", "white circular button with right arrow")
    left_arrow.set_element_as("CLICKABLE")  # Left arrow is clickable.
    right_arrow.set_element_as("CLICKABLE")  # Right arrow is clickable.

    # Frame 2: Target icon and number
    frame_2 = frames[2]
    # Frame 2 is dependent on Frame 1 and provides context, so it is not interactable.

    # Frame 3: Submit button
    frame_3 = frames[3]
    submit_button = frame_3.get_element("down", "Submit button on dark background")
    submit_button.set_element_as("NEXT")  # Submit button is used to complete the task.

    return {
        "Frame 0": {"interactable": "POINTABLE"},
        "Frame 1": {"elements": [
            {"position": "left", "interactable": "CLICKABLE"},
            {"position": "right", "interactable": "CLICKABLE"}
        ]},
        "Frame 2": {"interactable": None},  # Dependent frame, not interactable.
        "Frame 3": {"elements": [
            {"position": "down", "interactable": "NEXT"}
        ]}
    }
    

def stage3(frames):
    # Extract the target number and icon from Frame 2
    target_image = frames[2].image
    target_icon = ask([target_image], "ignore the number, describe the icon", answer_type="str")[0]
    target_orbit = ask([target_image], "ignore icon, what is the number?", answer_type="int")[0]

    # Get all choices in Frame 1
    left_arrow = frames[1].get_interactable(0)
    right_arrow = frames[1].get_interactable(1)
    choices = get_all_choices(left_arrow, right_arrow, frames[1])

    # Compare each choice with the target criteria
    comparison = compare([choice.image for choice in choices], f"Which image has the icon '{target_icon}' in orbit '{target_orbit}'?", target_image)

    # Select the correct choice
    for choice, is_correct in zip(choices, comparison):
        if is_correct:
            choice.select()
            break

    # Click the submit button in Frame 3
    submit_button = frames[3].get_interactable(0)
    click(submit_button)