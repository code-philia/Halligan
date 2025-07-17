from halligan.utils.action_tools import slide_x
from halligan.utils.vision_tools import rank


def stage1(frames):
    return


def stage2(frames):
    # Frame 2 contains the slider, which is the main interactable element
    slider = frames[2].get_element(position='left', details='blue button with an arrow pointing right')
    slider.set_element_as(interactable='SLIDEABLE_X')

    # Frame 1 is dependent on Frame 2, so it should not be marked as interactable
    # Frame 0 is also dependent on Frame 2, so it should not be marked as interactable


def stage3(frames):
    # Get the slider handle from Frame 2
    slider_handle = frames[2].get_interactable(0)

    # Slide the handle to the right while observing changes in Frame 1
    observations = slide_x(slider_handle, direction="right", observe_frame=frames[1])

    # Extract images from observations
    images = [choice.image for choice in observations]

    # Rank the images based on the task objective: completing the puzzle
    ranked_ids = rank(images, task_objective="Complete the image puzzle")

    # Select the best choice based on the highest rank
    best_choice = observations[ranked_ids[0]]

    # Refine the search around the best choice
    refined_choices = best_choice.refine()

    # Further rank the refined choices
    refined_images = [choice.image for choice in refined_choices]
    refined_ranked_ids = rank(refined_images, task_objective="Complete the image puzzle")

    # Select the best refined choice
    final_choice = refined_choices[refined_ranked_ids[0]]

    # Release the slider at the best position
    final_choice.release()