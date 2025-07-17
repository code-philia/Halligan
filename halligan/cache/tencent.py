from halligan.utils.action_tools import point
from halligan.utils.vision_tools import ask


def stage2(frames):
    # Frame 0 provides instructions, so it is non-interactable
    # Frame 1 contains the objects to interact with

    # Get Frame 1
    frame1 = frames[1]

    # Mark Frame 1 as POINTABLE since it contains multiple objects
    frame1.set_frame_as(interactable="POINTABLE")

    # Return the modified frames
    return frames


def stage3(frames) -> None:
    # Step 1: Locate the letter 'm' in Frame 1
    keypoint_image = frames[1].show_keypoints(region="all")
    m_keypoint_id = ask([keypoint_image], "point to the letter 'm'", answer_type="int")[0]
    m_keypoint = frames[1].get_keypoint(id=m_keypoint_id)

    # Step 2: Identify the object directly below the letter 'm'
    neighbour_image = m_keypoint.show_neighbours()
    object_below_id = ask([neighbour_image], "point to the object directly below the letter 'm'", answer_type="int")[0]
    object_below_keypoint = m_keypoint.get_neighbour(id=object_below_id)

    # Step 3: Click on the identified object
    point(to=object_below_keypoint)