from halligan.utils.vision_tools import rank
from halligan.utils.action_tools import slide_x


def stage1(frames):
    return


def stage2(frames: list):
    # Frame 0: Instructions, not interactable
    # Frame 1: Puzzle, dependent on Frame 2, not interactable
    # Frame 2: Contains the slider, which is interactable

    # Get the slider element in Frame 2
    slider_element = frames[2].get_element(position='left', details='blue arrow button')
    
    # Mark the slider element as SLIDEABLE_X
    slider_element.set_element_as(interactable='SLIDEABLE_X')


def stage3(frames: list) -> None:
    # Get the slider handle from Frame 2
    slider_handle = frames[2].get_interactable(0)

    # Slide the handle to the right while observing changes in Frame 1
    observations = slide_x(slider_handle, direction="right", observe_frame=frames[1])

    # Extract images from observations
    images = [choice.image for choice in observations]

    # Rank the images based on the task objective: completing the puzzle
    ranked_ids = rank(images, task_objective="Complete the puzzle")

    # Select the best choice based on the highest rank
    best_choice = observations[ranked_ids[0]]

    # Refine the search around the best choice
    refined_choices = best_choice.refine()

    # Further rank the refined choices
    refined_images = [choice.image for choice in refined_choices]
    refined_ranked_ids = rank(refined_images, task_objective="Complete the puzzle")

    # Select the best refined choice
    final_choice = refined_choices[refined_ranked_ids[0]]

    # Release the slider at the best position
    final_choice.release()