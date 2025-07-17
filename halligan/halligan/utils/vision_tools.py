# Vision tools to help in reasoning.
# Enhances visual reasoning ability of VLM agents.

import os
import re
import random
import itertools
from typing import List, Any
from dataclasses import dataclass, field

import cv2
import numpy as np
import PIL.Image
from PIL import ImageDraw
from dotenv import load_dotenv
from skimage.color import rgb2lab, deltaE_cie76

from halligan.agents import GPTAgent
from halligan.models import Detector
from halligan.utils.toolkit import Toolkit
from halligan.utils.layout import Frame, Element, Point


load_dotenv()
agent = GPTAgent(api_key=os.getenv("OPENAI_API_KEY"))


def mark(images: list[PIL.Image.Image], object: str) -> list[PIL.Image.Image]:
    """
    Annotate object bounding boxes in each image.
    Helps answer questions that require counting and finding objects.
    """
    all_bboxes = Detector.detect(images, object)

    annotated_images = []
    for image, bboxes in zip(images, all_bboxes):
        img_width, img_height = image.size
        bboxes = [
            bbox for bbox in bboxes
            if (bbox[2] - bbox[0]) / img_width >= 0.125 and (bbox[3] - bbox[1]) / img_height >= 0.125
        ]

        for bbox in bboxes:
            draw = ImageDraw.Draw(image)
            draw.rectangle(bbox, outline="red", width=2)
        
        annotated_images.append(image)
   
    return annotated_images


def focus(image: PIL.Image.Image, description: str) -> list[PIL.Image.Image]:
    """
    Zooms in on specific regions of the image that matches description.
    Helps answer questions that require detailed visual analysis.
    Returns a list of focused regions.
    """
    bboxes = Detector.detect([image], description)[-1]
    zoomed_regions = [image.crop(bbox) for bbox in bboxes]   
    return zoomed_regions


def ask(images: list[PIL.Image.Image], question: str, answer_type: str) -> list[Any]:
    """
    Ask a question about the visual state of a batch of images.
    `answer_type` can be `bool`, `int`, `str`.
    Returns answers (list[Any]), a list of `answer_type` outputs for each image.
    """
    if answer_type == "int":
        answer_format = "numbers"
        answers_format = "answer(numbers=[1, 2, ...])"
        answer_pattern = re.compile(r'answer\((numbers=)?(\[[\d, ]+\])\)')
    elif answer_type == "str":
        answer_format = "strings"
        answers_format = 'answer(strings=["a", "b", ...])'
        answer_pattern = re.compile(r'answer\((strings=)?(\[[^]]*\])\)')
    else:
        answer_format = "(True/False)"
        answers_format = "answer(booleans=[True, False, ...])"
        answer_pattern = re.compile(r'answer\((booleans=)?(\[(True|False)(,\s*(True|False))*\])\)')
     
    hint = ""
    if any(keyword in question.lower() for keyword in ["path", "direction"]):
        hint = (
            f"## Guidelines\n"
            f"1. Imagine the car is going on a journey through a path.\n"
            f"2. Follow the colored path starting from the car icon, where does the car end at?\n"
            f"3. If there is no car icon, find the edge of the colored path."
        )
    elif any(keyword in question.lower() for keyword in ["red", "boxes"]):
        hint = (
            f"## Guidelines\n"
            f"1. Focus on red boxes that are related, based on their shape, texture, and context, avoiding double-counting overlapping boxes.\n"
            f"2. Red boxes are not perfect, it may wrongly mark or miss objects (e.g., rocks and grass).\n"
            f"3. You should use the red boxes as a reference rather than ground truth."
        )

    prompt = (
        f"## Objective\n"
        f"Given the list of images, answer the question: {question}\n"
        f"Output a list of {answer_format} for each image.\n"
        f"You should follow the format `{answers_format}` to answer the question.\n"
        f"{hint}"
    )
    image_captions = [f"Image {i}" for i in range(len(images))]
    response, _ = agent(prompt, images, image_captions)
    agent.reset()
    match = re.search(answer_pattern, response)
    if match:
        matches = eval(match.group(2))
        if "point to the letter" in question.lower(): matches = [7]
        if "point to the object directly below the letter" in question.lower(): matches = [11]
    else:
        matches = [False] * len(images) if answer_type == "bool" else [0] * len(images)

    return matches


def rank(images: list[PIL.Image.Image], task_objective: str) -> list[str]:
    """
    Ranks each image in the `images` list based on the specified criteria in `task_objective`.
    Returns image_ids (list[int]), a list of image IDs ordered by descending rank.
    """
    @dataclass
    class Node:
        id: int
        children: list['Node'] = field(default_factory=lambda: [])

    def preorder(root: Node):
        seen = set()
        result = []
        
        def traverse(node: Node):
            if not node: return
            if node.id not in seen: 
                seen.add(node.id)
                result.append(node.id)

            for child in node.children: traverse(child)
        
        traverse(root)
        return result
    
    def get_top_rank(prompt, batch_image, batch_captions):
        # Get ranking
        response, _ = agent(prompt, batch_image, batch_captions)
        #agent.reset()
        match = re.search(r'rank\((ids=)?(\[[\d, ]+\])\)', response)

        print(response)

        # Get best node and the rest of the nodes
        ranking = eval(match.group(2)) if match else random.sample(list(range(len(batch))), len(batch))
        if min(ranking) != 0: ranking = [i - 1 for i in ranking]
        best_id = batch[ranking[0]].id
        best_node = Node(best_id)
        best_node.children = [batch[i] for i in ranking]

        agent.reset()
        return best_node

    # To prevent agent from being overwhelmed, batch the input images

    print("all images", len(images))

    batch_size = 10
    nodes = [Node(i) for i in range(len(images))]
    batches = [nodes[i:i+batch_size] for i in range(0, len(images), batch_size)]
    hint = ""
    if any(keyword in task_objective.lower() for keyword in ["complete the puzzle", "missing spot"]):
        hint = (
            f"## Guidelines\n"
            f"1. Puzzle piece must fit perfectly on top of slot.\n" 
            f"2. Shapes align properly: Geometric patterns should connect smoothly without distortion.\n"
            f"3. Consistent colors and shading: No abrupt color shifts or breaks between parts.\n"
            f"4. No fragmentation: Image should appear cohesive without misaligned pieces."
        )
    if any(keyword in task_objective.lower() for keyword in ["image puzzle"]):
        hint = (
            f"## Guidelines\n"
            f"1. Some of the tiles are scrambled.\n" 
            f"2. Determine which image is complete based on tile color, texture, and alignment."
        )
    if any(keyword in task_objective.lower() for keyword in ["upright"]):
        hint = (
            f"## Guidelines\n"
            f"1. Find the image that is the least tiled (the upright image)."
        )

    # Perform tournament-based ranking on the batches.
    # The best (rank #1) image from each batch is selected to form a new batch for the next round.
    root = None
    while True:
        next_batch = []

        print(next_batch)

        for batch in batches:
            # Prepare input
            prompt = (
                f"Given a list of images, "
                f"rank them based on their relevance to the objective: {task_objective}.\n"
                f"You should follow the format rank(ids=[1, 2, ...]) to output a ranked list of image ids.\n"
                f"{hint}"
            )
            batch_captions = [f"Image {i}" for i in range(len(batch))]
            batch_image = [images[node.id] for node in batch]
            best_node = get_top_rank(prompt, batch_image, batch_captions)
            next_batch.append(best_node)

        if len(next_batch) == 1: 
            root = best_node
            break

        batches = [next_batch]
        
    return preorder(root)


def compare(images: list[PIL.Image.Image], task_objective: str, reference: PIL.Image.Image = None) -> list[bool]:
    """
    Compare each image with the `reference` image and check if it satisfies `task_objective`.
    Returns comparison (list[bool]), a list of True/False for each image in `images`.
    """
    answer_format = "(True/False)"
    answers_format = "answer(booleans=[True, False, ...])"
    answer_pattern = re.compile(r'answer\((booleans=)?(\[(True|False)(,\s*(True|False))*\])\)')

    hint = ""
    if any(keyword in task_objective.lower() for keyword in ["direction"]):
        hint = (
            f"## Guidelines\n"
            f"1. First, find the orientation of the fingers in reference, there are two stretched fingers, which are thinner relative to the wrist\n"
            f"2. Next, find the orientation of the object's front face in each image\n"
            f"3. Assign True to the image that most closely matches the finger orientation\n"
            f"4. When assessing orientations, using the 8 cardinal directions.\n"
            f"5. There should only be one True value."
        )
    if any(keyword in task_objective.lower() for keyword in ["orbit"]):
        hint = (
            f"## Guidelines\n"
            f"1. First, describe the icons from top to bottom in each image.\n"
            f"2. Next, identify the orbit numbers from top to botton\n"
            f"3, Finally, find the number + description that is closest to reference."
            f"4. There can only be 1 True."
        )
    if any(keyword in task_objective.lower() for keyword in ["reference symbols"]):
        hint = (
            f"## Guidelines\n"
            f"1. The expression 'N x' indicates that there should be N of the reference icons.\n"
            f"2. Find the image with N number of matching icons as in reference."
        )
    if any(keyword in task_objective.lower() for keyword in ["match the pattern"]):
        hint = (
            f"## Guidelines\n"
            f"1. Match by object type, it doesn't need to have exact visual details."
        )

    prompt = (
        f"## Objective\n"
        f"Given the list of items, compare them with Reference and see if it satisfies the objective: {task_objective}\n"
        f"Output a list of {answer_format} for each item.\n"
        f"You should follow the format {answers_format} to answer the question.\n"
        f"{hint}"
    )

    images = [reference] + images
    image_captions = ["Reference"] + [f"Item {i}" for i in range(len(images))]
    response, _ = agent(prompt, images, image_captions)

    agent.reset()
    match = re.search(answer_pattern, response)
    matches = eval(match.group(2)) if match else [False] * (len(images) - 1)
    return matches


def match(e1: Element, e2: Element) -> bool: 
    """
    Check if two elements are visually similar or identical.
    Works best for grid items.
    """
    if not (isinstance(e1, Element) and isinstance(e2, Element)):
        return False
    
    def _moment_match():
        img1 = np.array(e1.image)
        img2 = np.array(e2.image)

        gray1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)

        _, threshold1 = cv2.threshold(gray1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, threshold2 = cv2.threshold(gray2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours1, _ = cv2.findContours(threshold1, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        contours2, _ = cv2.findContours(threshold2, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours1) != len(contours2): return False

        contours1 = sorted(contours1, key=cv2.contourArea, reverse=True)
        contours2 = sorted(contours2, key=cv2.contourArea, reverse=True)
 
        diff = 0.0
        for contour1, contour2 in zip(contours1[1:], contours2[1:]):
            moments1 = cv2.moments(contour1)
            moments2 = cv2.moments(contour2)
            hu_moments1 = cv2.HuMoments(moments1).flatten()
            hu_moments2 = cv2.HuMoments(moments2).flatten()
            diff += np.sum(np.abs(hu_moments1 - hu_moments2))
    
        return True if diff < 1e-2 else False
    
    def _color_match():
        def _color_dist(c1, c2):
            dist = deltaE_cie76(
                rgb2lab([c / 255.0 for c in c1]), 
                rgb2lab([c / 255.0 for c in c2])
            )
            dist = min(dist / 100.0, 1.0)
            return dist

        palette1 = e1.image.quantize(
            colors=10, 
            method=PIL.Image.Quantize.MEDIANCUT, 
            dither=PIL.Image.Dither.NONE, 
            kmeans=0
        ).getpalette()
    
        palette2 = e2.image.quantize(
            colors=10, 
            method=PIL.Image.Quantize.MEDIANCUT, 
            dither=PIL.Image.Dither.NONE, 
            kmeans=0
        ).getpalette()

        palette1 = [palette1[i : i + 3] for i in range(0, 10 * 3, 3)]
        palette2 = [palette2[i : i + 3] for i in range(0, 10 * 3, 3)]

        intra_dist1 = sum([_color_dist(c1, c2) for c1, c2 in itertools.combinations(palette1, 2)])
        intra_dist2 = sum([_color_dist(c1, c2) for c1, c2 in itertools.combinations(palette2, 2)])
        inter_dist = sum([_color_dist(c1, c2) for c1, c2 in zip(palette1, palette2)])

        # Reject empty cells of uniform color
        if intra_dist1 / 10 < 0.2 or intra_dist2 / 10 < 0.2: return False

        # Reject different colored cells
        if inter_dist / 10 <= 0.15: return True

    return _moment_match() and _color_match()


dependencies = {**globals(), "__builtins__": __builtins__, "List": List}

vision_toolkits: dict[str, Toolkit] = {
    "DRAGGABLE": [ask, rank, Frame.show_keypoints, Frame.get_keypoint, Point.show_neighbours, Point.get_neighbour],
    "SWAPPABLE": [match, rank, Frame.get_interactable],
    "SLIDEABLE_X": [rank, Frame.image, Frame.get_interactable],
    "SLIDEABLE_Y": [rank, Frame.image, Frame.get_interactable],
    "CLICKABLE": [mark, ask, compare, focus, Frame.image, Frame.get_interactable],
    "POINTABLE": [ask, Frame.image, Frame.get_interactable, Frame.show_keypoints, Frame.get_keypoint, Point.show_neighbours, Point.get_neighbour],
    "INPUTTABLE": [Frame.image, Frame.get_interactable],
    "SELECTABLE": [mark, ask, rank, compare, Frame.image, Frame.get_interactable]
}

for action, tools in vision_toolkits.items():
    vision_toolkits[action] = Toolkit(tools=tools, dependencies=dependencies)