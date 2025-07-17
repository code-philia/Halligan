from halligan.utils.vision_tools import ask, rank
from halligan.utils.action_tools import drag


def stage1(frames):
    return


def stage2(frames):
    # Frame 0: Instruction frame, no interactables
    frame_0 = frames[0]
    frame_0.set_frame_as("POINTABLE")  # Instructional frame, no direct interaction

    # Frame 1: Puzzle frame
    frame_1 = frames[1]

    # Identify the puzzle piece options
    puzzle_piece_1 = frame_1.get_element(position="down", details="leftmost puzzle piece")
    puzzle_piece_2 = frame_1.get_element(position="down", details="middle puzzle piece")
    puzzle_piece_3 = frame_1.get_element(position="down", details="rightmost puzzle piece")

    # Mark the puzzle pieces as DRAGGABLE
    puzzle_piece_1.set_element_as("DRAGGABLE")
    puzzle_piece_2.set_element_as("DRAGGABLE")
    puzzle_piece_3.set_element_as("DRAGGABLE")

    
def stage3(frames):
    # Step 1: Annotate the missing slot in the fox image with keypoints
    keypoint_image = frames[1].show_keypoints(region="all")

    # Step 2: Ask the user to identify the general area of the missing slot
    missing_slot_id = ask([keypoint_image], "Where is the puzzle slot in the image?", answer_type="int")[0]
    missing_slot = frames[1].get_keypoint(id=missing_slot_id)

    # Step 3: Narrow down the search space using the neighbors of the identified keypoint
    neighbour_image = missing_slot.show_neighbours()
    refined_slot_id = ask([neighbour_image], "Refine the puzzle slot location.", answer_type="int")[0]
    refined_slot = missing_slot.get_neighbour(id=refined_slot_id)

    # Step 4: Drag the correct puzzle piece to the refined missing slot
    # Preview the draggable options
    drag_choices = []
    for i in range(3):
        piece = frames[1].get_interactable(i)
        drag_choices.extend(drag(start=piece, end=refined_slot))

    # Rank the draggable options to find the best match
    best_match_id = rank([choice.preview for choice in drag_choices], "Puzzle is fully in the missing spot")[0]

    # Drag and drop the best match
    drag_choices[best_match_id].drop()