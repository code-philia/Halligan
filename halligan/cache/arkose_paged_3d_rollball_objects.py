from halligan.utils.vision_tools import mark, compare
from halligan.utils.action_tools import get_all_choices, click


def stage1(frames):
    return


def stage2(frames):
    # Frame 0: Instructions, not interactable
    # Frame 1: Contains the car and arrows
    left_arrow = frames[1].get_element('left', 'left arrow button')
    right_arrow = frames[1].get_element('right', 'right arrow button')
    left_arrow.set_element_as('CLICKABLE')
    right_arrow.set_element_as('CLICKABLE')
    
    # Frame 2: Hand direction, not interactable
    # Frame 3: Submit button
    submit_button = frames[3].get_element('up', 'Submit button')
    submit_button.set_element_as('NEXT')


def stage3(frames):
    # Get the interactable elements for navigation
    left_arrow = frames[1].get_interactable(0)
    right_arrow = frames[1].get_interactable(1)
    
    # Get the target direction from Frame 2
    target_image = frames[2].image

    # Cycle through all choices in Frame 1
    choices = get_all_choices(left_arrow, right_arrow, frames[1])
    
    # Mark the images for comparison
    marked_images = mark([choice.image for choice in choices], "object")
    
    # Compare each choice with the target direction
    ranking = compare(marked_images, "Which image has the object aligned with the direction of the hand?", target_image)
    
    # Select the best choice
    choices[ranking.index(True)].select()

    # Click the submit button in Frame 3
    submit_button = frames[3].get_interactable(0)
    click(submit_button)