from halligan.utils.action_tools import select
from halligan.utils.vision_tools import ask, mark


def stage1(frames):
    return


def stage2(frames):
    # Frame 0: Instruction frame, dependent frame, non-interactable
    frame_0 = frames[0]
    
    # Frame 1: Contains the cards to interact with
    frame_1 = frames[1]
    
    # Split Frame 1 into selectable subframes (each containing a pair of cards)
    subframes = frame_1.split(rows=2, columns=3)
    
    # Mark each subframe as SELECTABLE
    for subframe in subframes:
        subframe.set_frame_as(interactable="SELECTABLE")
    
    # Return the interactable structure
    return {
        "frames": [
            {"frame": frame_0, "interactable": None},  # Frame 0 is non-interactable
            {"frame": frame_1, "interactable": "SELECTABLE"}  # Frame 1 is selectable
        ]
    }


def stage3(frames: list) -> None:
    # Extract images from all selectable frames
    images = [frame.image for frame in frames[1:]]
    
    # Mark the cards in each frame for identification
    marked_images = mark(images, "card")
    
    # Ask the tool to identify matching cards
    matching_cards = ask(marked_images, "Which cards match based on their symbols, numbers, and colors?", answer_type="bool")
    
    # Select the frames with matching cards
    for i, match in enumerate(matching_cards):
        if match:
            select(frames[i + 1])