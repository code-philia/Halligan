from halligan.utils.vision_tools import mark, ask
from halligan.utils.action_tools import select


def stage1(frames):
    return


def stage2(frames):
    # Frame 0 is the instruction frame and is not interactable
    # Frame 1 contains the grid of images
    frame_1 = frames[1]
    
    # Split Frame 1 into a grid of selectable subframes
    subframes = frame_1.split(rows=2, columns=3)
    
    # Mark each subframe as SELECTABLE
    for subframe in subframes:
        subframe.set_frame_as(interactable="SELECTABLE")


def stage3(frames):
    # Mark animals in each frame
    marked_images = mark([frame.image for frame in frames[1:]], "animal")
    
    # Count the number of animals in each marked image
    animal_counts = ask(marked_images, "What is the number of animals in the marked red boxes?", answer_type="int")
    
    # Extract the number shown in each image
    numbers_in_images = ask([frame.image for frame in frames[1:]], "What is the number in the image?", answer_type="int")
    
    # Find the frame where the number is closest to the count of animals
    differences = [abs(animal_count - number) for animal_count, number in zip(animal_counts, numbers_in_images)]
    best_match_index = differences.index(min(differences))
    
    # Select the frame with the closest match
    select(frames[best_match_index + 1])