from halligan.utils.action_tools import get_all_choices, click
from halligan.utils.vision_tools import mark, ask


def stage1(frames):
    return


def stage2(frames):
    # Frame 0 provides instructions, so it's not interactable
    # Frame 1 has arrows to select the group of rocks
    frame1 = frames[1]
    left_arrow = frame1.get_element('left', 'black circle with left arrow')
    right_arrow = frame1.get_element('right', 'black circle with right arrow')
    left_arrow.set_element_as('CLICKABLE')
    right_arrow.set_element_as('CLICKABLE')
    
    # Frame 2 displays the number, it's not interactable
    # Frame 3 has the 'Submit' button
    frame3 = frames[3]
    submit_button = frame3.get_element('center', 'Submit button')
    submit_button.set_element_as('NEXT')


def stage3(frames):
    # Get the target number of rocks from Frame 2
    target_number = ask([frames[2].image], "What is the number shown?", answer_type="int")[0]

    # Get all choices of rock groups from Frame 1
    left_arrow = frames[1].get_interactable(0)
    right_arrow = frames[1].get_interactable(1)
    choices = get_all_choices(left_arrow, right_arrow, frames[1])

    # Initialize variables to track the best choice
    best_choice = None
    best_difference = float('inf')

    # Iterate through each choice to find the closest match
    for choice in choices:
        # Mark rocks in the current choice image
        marked_image = mark([choice.image], "rock")
        # Count the number of rocks
        rock_count = ask(marked_image, "What is the number of rocks in the marked red boxes?", answer_type="int")[0]

        # Calculate the difference from the target
        difference = abs(target_number - rock_count)

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