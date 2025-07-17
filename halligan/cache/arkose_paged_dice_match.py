from halligan.utils.vision_tools import ask, focus
from halligan.utils.action_tools import get_all_choices, click


def stage1(frames):
    return


def stage2(frames):
    # Frame 0: Instructions
    frame_0 = frames[0]
    frame_0.set_frame_as(interactable="POINTABLE")

    # Frame 1: Dice with arrows
    frame_1 = frames[1]
    left_arrow = frame_1.get_element(position="left", details="black circle with left arrow")
    right_arrow = frame_1.get_element(position="right", details="black circle with right arrow")
    left_arrow.set_element_as(interactable="CLICKABLE")
    right_arrow.set_element_as(interactable="CLICKABLE")

    # Frame 2: Target number
    # This frame is dependent and non-interactable

    # Frame 3: Submit button
    frame_3 = frames[3]
    submit_button = frame_3.get_element(position="center", details="Submit button")
    submit_button.set_element_as(interactable="NEXT")


def stage3(frames):
    # Extract the target number from Frame 2
    target_image = frames[2].image
    target_number = ask([target_image], "What is the target number?", answer_type="int")[0]

    # Get all possible dice configurations by cycling through choices
    left_arrow = frames[1].get_interactable(0)
    right_arrow = frames[1].get_interactable(1)
    choices = get_all_choices(left_arrow, right_arrow, frames[1])

    # Initialize variables to track the best choice
    best_choice = None
    best_difference = float('inf')

    # Iterate through each choice to find the closest sum to the target number
    for choice in choices:
        # Focus on the dice in the current choice
        dice_patches = focus(choice.image, "dice")
        dice_numbers = ask(dice_patches, "What is the die number?", answer_type="int")
        dice_sum = sum(dice_numbers)

        # Calculate the difference from the target
        difference = abs(target_number - dice_sum)

        # Update the best choice if this one is closer
        if difference < best_difference:
            best_difference = difference
            best_choice = choice

    # Select the best choice
    if best_choice:
        best_choice.select()

    # Click the submit button in Frame 3
    submit_button = frames[3].get_interactable(0)
    click(submit_button)