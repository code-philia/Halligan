from halligan.utils.vision_tools import mark, compare
from halligan.utils.action_tools import get_all_choices, click


def stage1(frames):
    return


def stage2(frames):
    # Frame 0: Instructions, related to Frame 1
    # Frame 1: Contains arrows for navigation
    left_arrow = frames[1].get_element(position='left', details='circular arrow')
    right_arrow = frames[1].get_element(position='right', details='circular arrow')
    left_arrow.set_element_as(interactable='CLICKABLE')
    right_arrow.set_element_as(interactable='CLICKABLE')
    
    # Frame 2: Symbols, related to Frame 3
    # No interactables needed here as per the task description
    
    # Frame 3: Submit button
    submit_button = frames[3].get_element(position='center', details='Submit button')
    submit_button.set_element_as(interactable='NEXT')


def stage3(frames):
    # Get the arrows for navigation in Frame 1
    left_arrow = frames[1].get_interactable(0)
    right_arrow = frames[1].get_interactable(1)

    # Get all choices by cycling through Frame 1
    choices = get_all_choices(left_arrow, right_arrow, frames[1])

    # Reference image from Frame 2
    reference_image = frames[2].image

    # Iterate through each choice to find the correct one
    for choice in choices:
        # Mark the objects in the current choice
        marked_image = mark([choice.image], "object")

        # Compare the marked image with the reference image
        comparison = compare(marked_image, "Does this match the reference symbols?", reference_image)

        # If the comparison is True, select this choice
        if comparison[0]:
            choice.select()
            break

    # Click the submit button in Frame 3
    submit_button = frames[3].get_interactable(0)
    click(submit_button)