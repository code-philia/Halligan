from halligan.utils.vision_tools import mark, ask
from halligan.utils.action_tools import select


def stage1(frames):
    return


def stage2(frames):
    # Frame 0 is the instruction frame and is not interactable
    frame_0 = frames[0]
    
    # Frame 1 contains the images and should be split into selectable subframes
    frame_1 = frames[1]
    
    # Split Frame 1 into a grid of selectable subframes
    subframes = frame_1.split(rows=2, columns=3)
    
    # Mark each subframe as SELECTABLE
    for subframe in subframes:
        subframe.set_frame_as(interactable="SELECTABLE")


def stage3(frames):
    # Mark the images to identify fingers
    marked_images = mark([frame.image for frame in frames[1:]], "fingers")
    
    # Ask how many fingers are in each marked image
    finger_counts = ask(marked_images, "What is the total number of fingers shown?", answer_type="int")
    
    # Find the image with the closest number of fingers to 4
    closest_index = min(range(len(finger_counts)), key=lambda i: abs(finger_counts[i] - 4))
    
    # Select the image with the closest count
    select(frames[closest_index + 1])