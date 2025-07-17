from halligan.utils.vision_tools import ask
from halligan.utils.action_tools import point, click


def stage1(frames):
    return


def stage2(frames):
    frame_0 = frames[0]
    submit_button = frame_0.get_element(position='down', details="orange button with 'Submit' text")
    submit_button.set_element_as(interactable='NEXT')
    frame_1 = frames[1]
    frame_1.set_frame_as(interactable='POINTABLE')
    return frames


def stage3(frames):
    # Step 1: Annotate the keypoints on the 3D grid map in Frame 1
    keypoint_image = frames[1].show_keypoints(region="all")

    # Step 2: Ask a question to identify the general area of the end of the orange path
    initial_answer = ask([keypoint_image], "Which keypoint is at the end of the colored path?", answer_type="int")

    # Step 3: Get the keypoint corresponding to the initial answer
    initial_keypoint = frames[1].get_keypoint(id=initial_answer[0])

    # Step 4: Narrow down the search space by showing neighbors of the initial keypoint
    neighbour_image = initial_keypoint.show_neighbours()

    # Step 5: Refine the answer by asking again within the narrowed-down space
    refined_answer = ask([neighbour_image], "Which keypoint is at the end of the colored path?", answer_type="int")

    # Step 6: Get the refined keypoint corresponding to the refined answer
    endpoint = initial_keypoint.get_neighbour(id=refined_answer[0])

    # Step 7: Place a dot at the identified keypoint
    point(to=endpoint)

    # Step 8: Click the 'Submit' button in Frame 0
    submit_button = frames[0].get_interactable(id=0)
    click(target=submit_button)