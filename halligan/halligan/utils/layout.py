from __future__ import annotations
import math
from abc import ABC
from typing import TypeAlias, Literal
from collections import Counter, deque, defaultdict

import cv2
import faiss
import numpy as np
import PIL.Image
from PIL import ImageDraw, ImageChops
from skimage.segmentation import slic
from skimage.measure import regionprops
from scipy.ndimage import binary_fill_holes

from halligan.utils.constants import InteractableElement, InteractableFrame
from halligan.models import CLIP, Segmenter


Position: TypeAlias = Literal["up", "down", "left", "right"]


class Component(ABC):
    def __init__(self, x: int, y: int, image: PIL.Image.Image) -> None:
        """Manages a region that is part of the screen.
        """
        self._image = image
        self.x = int(x)
        self.y = int(y)
        self.w = image.size[0]
        self.h = image.size[1]
        self.interactable: str = None # Stage 2: Interactable type

    @property
    def bbox(self) -> list[int, int, int, int]:
        return [self.x, self.y, self.x + self.w, self.y + self.h]
        
    @property
    def region(self) -> list[int, int, int, int]:
        return [self.x, self.y, self.w, self.h]
    
    @property
    def center(self) -> tuple[int, int]:
        return self.x + (self.w // 2), self.y + (self.h // 2)

    def is_within(self, Component: Component) -> bool:
        xmin1, ymin1, xmax1, ymax1 = self.bbox
        xmin2, ymin2, xmax2, ymax2 = Component.bbox
        return (
            xmin2 <= xmin1 <= xmax2 and
            ymin2 <= ymin1 <= ymax2 and
            xmin2 <= xmax1 <= xmax2 and
            ymin2 <= ymax1 <= ymax2
        )
    

class Frame(Component):
    def __init__(self, x: int, y: int, image: PIL.Image.Image) -> None:
        """An image can be decomposed into frames.
        """
        super().__init__(x, y, image)
        # Visual description of the frame
        self.description: str = ""

        # Tracks relations with other frames
        self.relations: dict[int, str] = {}

        # Tracks subframes
        self.subframes: list[Frame] = []

        # Tracks annotated interactable elements
        self.interactables: list[Element] = []

        # Tracks detected keypoints
        self.keypoints: list[tuple] = []

        # Tracks all segmented elements
        self._elements: dict[Position, list[Element]] = None
        self._indexes: dict[Position, faiss.Index] = None
    
    @property
    def image(self) -> PIL.Image.Image:
        """
        Each frame has a referenceable image for processing/analysis.
        """
        return self._image

    def get_element(self, position: Position, details: str) -> Element:
        """
        Get one specific element by its relative position in the frame and its detailed visual description.
        Elements can be marked as interactables.
        position: where is the element
        details: color, shape, and visual features of the element
        """
        if self._elements is None or self._indexes is None:
            self._segment()
        
        elements = self._elements.get(position, self._elements["all"])

        if not elements: 
            return Element(self.x, self.y, self._image, self)
        
        index = self._indexes.get(position, self._indexes["all"])
        text_feature = CLIP.get_text_features(details)

        text_feature = text_feature / np.linalg.norm(text_feature, ord=2, axis=-1, keepdims=True)
        _, matches = index.search(text_feature, k=5)

        # Return the first element that was not annotated
        for index in matches[0]:
            element: Element = elements[index]
            if not element.retrieved:
                element.retrieved = True
                return element
        
        # If all elements were annotated, return the best match
        return elements[matches[0][0]]
    
    def get_interactable(self, id: int) -> Element:
        """
        Get an interactable element in the frame by its id.
        """
        return self.interactables[id] if self.interactables else self
    
    def get_keypoint(self, id: int) -> Point:
        """
        Get a keypoint in the frame by its id.
        """
        return self.keypoints[id]
    
    def show_keypoints(self, region: Literal['all', 'top', 'bottom', 'left', 'right']) -> PIL.Image.Image:
        """
        Annotate keypoints on the Frame. Each keypoint has a number ID.
        Keypoints allows you to work in 2D spaces (drag-and-drop / drawing / pointing).
        Returns
            image (PIL.Image.Image): The frame image with all keypoints annotated on it.
        """
        if region == "top":
            img = self.image.crop((0, 0, self.w, self.h // 2))
            x_offset, y_offset = 0, 0
        elif region == "bottom":
            img = self.image.crop((0, self.h // 2, self.w, self.h))
            x_offset, y_offset = 0, self.h // 2
        elif region == "left":
            img = self.image.crop((0, 0, self.w // 2, self.h))
            x_offset, y_offset = 0, 0
        elif region == "right":
            img = self.image.crop((self.w // 2, 0, self.w, self.h))
            x_offset, y_offset = self.w // 2, 0
        else:
            img = self.image
            x_offset, y_offset = 0, 0

        img = np.array(img)
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        h, w, _ = img.shape

        # Compute the number of SLIC segments based on image size
        size = max(1, round(h / 100)) * max(1, round(w / 100))
        n_segments = 25 if size <= 4 else 100

        # Step 1: Generate superpixels using SLIC
        segments = slic(img, n_segments=n_segments, compactness=10)
        
        # Step 2: Compute the saliency map using OpenCV's saliency detection
        saliency = cv2.saliency.StaticSaliencySpectralResidual_create()
        (_, saliency_map) = saliency.computeSaliency(img)
        saliency_map = (saliency_map * 255).astype("uint8")
        regions = regionprops(segments)

        # Step 3: Filter centroids based on saliency
        saliency_scores = []
        for props in regions:
            cy, cx = map(int, props.centroid) 
            superpixel_mask = segments == props.label
            avg_saliency = np.mean(saliency_map[superpixel_mask])
            saliency_scores.append((avg_saliency, cx, cy))

        saliency_values = [score[0] for score in saliency_scores]
        threshold = np.percentile(saliency_values, 50)
        keypoints = [(cx, cy) for avg_saliency, cx, cy in saliency_scores if avg_saliency > threshold]

        for (cx, cy) in keypoints:
            image = self.image.crop(box=(cx, cy, cx + 1, cy + 1))
            self.keypoints.append(Point(self.x + x_offset + cx, self.y + y_offset + cy, image, self))

        annotated_img = img.copy()
        for j, keypoint in enumerate(keypoints):
            cx, cy = keypoint
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            cv2.putText(annotated_img, str(j), (cx, cy), font, font_scale, (255,255,255), 3, cv2.LINE_AA)
            cv2.putText(annotated_img, str(j), (cx, cy), font, font_scale, (0,0,0), 1, cv2.LINE_AA)

        return PIL.Image.fromarray(annotated_img)

    def split(self, rows: int, columns: int) -> list[Frame]:
        """
        Split the entire frame into SELECTABLE subframes.
        """
        width, height = self.image.size

        # Agent may misplace (rows, cols), readjust based on aspect ratio
        if width > height: columns, rows = max(columns, rows), min(columns, rows)
        if width <= height: columns, rows = min(columns, rows), max(columns, rows)
    
        choice_width, choice_height = width // columns, height // rows
        choices = []
        for i in range(rows):
            for j in range(columns):
                x = j * choice_width
                y = i * choice_height
                image = self.image.crop(box=(x, y, x + choice_width, y + choice_height))
                choice = Frame(self.x + x, self.y + y, image)
                choices.append(choice)

        self.subframes = choices
        return choices

    def grid(self, tiles: int) -> list[list[Element]]:
        """
        Convert the frame into multiple SWAPPABLE tile elements.
        tiles: total column * row cells.
        """
        width, height = self.image.size
        aspect_ratio = width / height

        # Agent may under/overestimate number of tiles, readjust based on aspect ratio
        cols = math.sqrt(tiles * aspect_ratio)
        cols = round(cols)
        rows = tiles / cols
        rows = round(rows)

        tile_w, tile_h = width // cols, height // rows
        _grid = []
        for i in range(rows):
            _tiles = []
            for j in range(cols):
                x = j * tile_w
                y = i * tile_h
                image = self.image.crop(box=(x, y, x + tile_w, y + tile_h))
                tile = Element(self.x + x, self.y + y, image, self)
                _tiles.append(tile)

            _grid.append(_tiles)

        self._elements = _grid
        return _grid

    def set_frame_as(self, interactable: str) -> None:
        """
        ( Docstring will be dynamically replaced by items in InteractableFrame. )
        """
        self.interactable = interactable

    def _segment(self) -> None:
        self._elements = defaultdict(list)
        self._indexes = {}

        # Segment the frame into elements
        bboxes, _, segments = Segmenter.segment(self.image)
        element_list = [
            Element(
                self.x + bbox[0], 
                self.y + bbox[1],
                segment,
                self
            ) for bbox, segment in zip(bboxes, segments)
        ]

        if not segments: return
        
        # Encode the visual features of each element
        element_features = CLIP.get_image_features(segments)

        # Group all elements by their position in frame region
        frame_center_x, frame_center_y = self.x + self.w / 2, self.y + self.h / 2

        positions = {
            "all": lambda x, y: True,
            "up": lambda x, y: y <= frame_center_y,
            "down": lambda x, y: y > frame_center_y,
            "left": lambda x, y: x <= frame_center_x, #and y > frame_center_y,
            "right": lambda x, y: x > frame_center_x #and y > frame_center_y
        }


        self._elements = defaultdict(list)
        self._indexes = {}
        
        
        self._elements = defaultdict(list)
        self._indexes = {}
        
        for position, check in positions.items():
            group: list[Element] = []
            features: list[np.ndarray] = []

            for element, feature in zip(element_list, element_features):
                if element.w > 300 or element.h > 300: continue

                element_center_x, element_center_y = element.x + element.w / 2, element.y + element.h / 2
                
                if check(element_center_x, element_center_y):
                    group.append(element)
                    features.append(feature)

            if features:
                index = faiss.IndexFlatIP(features[-1].shape[0])
                index.add(np.array(features))
                
                self._elements[position] = group
                self._indexes[position] = index


class Element(Component):
    def __init__(self, x: int, y: int, image: PIL.Image.Image, parent: Frame) -> None:
        """A frame contains elements.
        """
        super().__init__(x, y, image)
        self.parent = parent
        self.retrieved = False

        if not self.is_within(parent): raise ValueError(f"{self} must be within {parent}")

    @property
    def image(self) -> PIL.Image.Image:
        """
        Each element has a referenceable image for processing/analysis.
        """
        return self._image
    
    @image.setter
    def image(self, value):
        self._image = value

    def set_element_as(self, interactable: str) -> None:
        """
        ( Docstring will be dynamically replaced by items in InteractableElement ).
        """
        self.interactable = interactable
        self.parent.interactables.append(self)


class Point(Component):
    def __init__(self, x: int, y: int, image: PIL.Image.Image, parent: Frame) -> None:
        """
        A frame contains keypoints
        """
        super().__init__(x, y, image)
        self.parent = parent
        self.neighbours = []

    def show_neighbours(self) -> PIL.Image.Image:
        """
        Reduce the search space for further analysis by narrowing down to keypoints surrounding this point.
        """
        # Relative to screen
        xmin = max(self.parent.x, self.x - 100)
        ymin = max(self.parent.y, self.y - 100)
        xmax = min(self.parent.x + self.parent.w, self.x + 100)
        ymax = min(self.parent.y + self.parent.h, self.y + 100)

        # Relative to parent frame
        region_img = self.parent.image.crop([
            xmin - self.parent.x, ymin - self.parent.y, 
            xmax - self.parent.x, ymax - self.parent.y
        ])
        region_img = np.array(region_img)
        region_img = cv2.cvtColor(region_img, cv2.COLOR_RGBA2RGB)

        annotated_img = self.parent.image.copy()
        annotated_img = np.array(annotated_img)
        segments = slic(region_img, n_segments=20, compactness=10)
        regions = regionprops(segments)
        for i, props in enumerate(regions):
            cy, cx = map(int, props.centroid) 

            # Relative to screen
            image = PIL.Image.new("RGB", (1, 1))
            self.neighbours.append(Point(xmin + cx, ymin + cy, image, self))

            # Relative to parent frame
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            px = xmin - self.parent.x + cx
            py = ymin - self.parent.y + cy
            cv2.putText(annotated_img, str(i), (px, py), font, font_scale, (255,255,255), 3, cv2.LINE_AA)
            cv2.putText(annotated_img, str(i), (px, py), font, font_scale, (0,0,0), 1, cv2.LINE_AA)

        return PIL.Image.fromarray(annotated_img)
    
    def get_neighbour(self, id: int) -> Point:
        """
        Get a neighbouring keypoint by its id.
        """
        return self.neighbours[id]


def get_frames(x: int, y: int, image: PIL.Image.Image) -> list[Frame]:
    """
    Extract frames from the image

    1. Pre-processing: Convert to greyscale, apply median blur, binarize with adaptive threshold
    2. Post-processing: Erode and dilate to remove noise, fill binary holes, find connected Components
    3. Filtering: Select all Components above threshold, crop Component from image as frame, mask Component from input image

    Args:
        x, y: position of image on screen
        image: input image

    Returns:
        A list of masked input image + image frames
    """
    def trim_margin(x: int, y: int, image: PIL.Image.Image) -> tuple[int, int, PIL.Image.Image]:
        """Remove margin surrounding the CAPTCHA challenge.
        """
        # Get the pixel colors from all 4 corners and do majority voting
        width, height = image.size
        corners = [image.getpixel((x, y)) for x, y in [(0, 0), (0, height - 1), (width - 1, 0), (width - 1, height - 1)]]
        counts = Counter(corners)
        majority_color, _ = counts.most_common(1)[0]

        # Crop margins with the majority color
        bg = PIL.Image.new(image.mode, image.size, majority_color)
        diff = ImageChops.difference(image, bg)
        bbox = diff.getbbox()
        if bbox:
            new_x, new_y = bbox[:2]
            return x + new_x, y + new_y, image.crop(bbox)
        else:
            return x, y, image
    
    def fill_margins(image: np.ndarray) -> np.ndarray:
        """
        Fill the margins of a binary image with white pixels.

        This function finds the largest white area in the binary image, 
        identifies its bounding box, and fills all pixels outside the 
        bounding box with white.

        Args:
            image: Binary input image with value range of (0, 255).

        Returns:
            np.ndarray: Image with margins filled with white pixels.
        """
        # Find all connected components
        _, _, stats, _ = cv2.connectedComponentsWithStats(image, connectivity=8)
        if stats.shape[0] <= 1: return image
        areas = stats[1:, cv2.CC_STAT_AREA]

        # Find the largest component by area
        largest_index = np.argmax(areas) + 1
        
        # Extract bounding box coordinates of the largest component
        x, y, w, h = stats[largest_index, cv2.CC_STAT_LEFT], stats[largest_index, cv2.CC_STAT_TOP], \
                    stats[largest_index, cv2.CC_STAT_WIDTH], stats[largest_index, cv2.CC_STAT_HEIGHT]
        
        # Copy the Component inside the bounding box from the original image
        if w * h < image.shape[0] * image.shape[1] * 0.9: return image
        result = np.ones_like(image) * 255
        result[y:y+h, x:x+w] = image[y:y+h, x:x+w]
        return result

    # Pre-processing
    image = image.copy()
    np_image = np.array(image)
    np_image = cv2.cvtColor(np_image, cv2.COLOR_BGRA2GRAY)
    np_image = cv2.medianBlur(np_image, 3)
    np_image = cv2.adaptiveThreshold(np_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Post-processsing
    kernel = np.ones((3, 3), np.uint8)
    np_image = cv2.morphologyEx(np_image, cv2.MORPH_ERODE, kernel, iterations=3)
    np_image = cv2.morphologyEx(np_image, cv2.MORPH_DILATE, kernel, iterations=3)
    np_image = fill_margins(np_image)
    np_image = cv2.bitwise_not(np_image)
    np_image = binary_fill_holes(np_image).astype(np.uint8) * 255
    _, _, stats, _ = cv2.connectedComponentsWithStats(image=np_image, connectivity=8)

    # Filtering
    frames: list[Frame] = []
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest_indices = np.argsort(areas)[::-1]
    draw = ImageDraw.Draw(image)

    for i in largest_indices:
        fx, fy, fw, fh = stats[i + 1, cv2.CC_STAT_LEFT], stats[i + 1, cv2.CC_STAT_TOP], \
                    stats[i + 1, cv2.CC_STAT_WIDTH], stats[i + 1, cv2.CC_STAT_HEIGHT] 
        
        # Keep the frame based on its relative size when compared to previous Component
        if frames:
            area = fw * fh
            prev_frame = frames[-1].image
            prev_area = prev_frame.size[0] * prev_frame.size[1] 
            if area < int(prev_area * 0.2): break
        
        # Create frame and mask its region from base image
        frame_image = image.crop(box=(fx, fy, fx + fw, fy + fh))
        frame = Frame(x + fx, y + fy, frame_image)
        frames.append(frame)
        draw.rectangle([fx, fy, fx + fw, fy + fh], fill=(255, 255, 255))

    # Consider base image as a frame
    new_x, new_y, image = trim_margin(x, y, image)
    frames.insert(0, Frame(new_x, new_y, image))
    return frames


def get_observation(frames: list[Frame]) -> tuple[
    list[Frame], list[PIL.Image.Image], list[str], list[str], list[str], set[str]
]:
    """
    Get the frame images, interactable element images, image descriptions, and frame relations.
    These constitute the VLM agent's observation of the environment.
    
    Args:
    - frames (List[Frame]): A list of Frame objects representing the environment.
    
    Returns:
    - A tuple containing:
    - List of visible frames
    - List of images from frames and interactable elements
    - List of captions corresponding to the images
    - List of relations between frames
    - List of descriptions for each frame
    - List of unique interactable types
    """

    # Step 1: Traverse frames and retrieve images, captions, and index ranges.
    # Only leaf nodes (frames without subframes) and their interactable elements are considered.
    all_frames = []
    images = []
    image_captions = []
    interactables = set()

    global_index = 0
    global_index_ranges = {i: None for i in range(len(frames))}

    queue = deque([(i, frame) for i, frame in enumerate(frames)])
    while queue:
        frame_index, frame = queue.popleft()
        
        if frame.subframes:
            queue.extendleft((frame_index, subframe) for subframe in reversed(frame.subframes))

        else:
            all_frames.append(frame)
            frame_interactable = ""
            if frame.interactable:
                interactables.add(frame.interactable)
                frame_interactable = f": {frame.interactable}"
            
            image_captions.append(f"Frame {global_index}{frame_interactable}")
            images.append(frame.image)
            
            for element_index, element in enumerate(frame.interactables):
                interactables.add(element.interactable)
                image_captions.append(f"Frame {global_index} Interactable {element_index}: {element.interactable}")
                images.append(element.image)

            if not global_index_ranges[frame_index]:
                # Initialize the index range with (start, end) as the same global index
                global_index_ranges[frame_index] = (global_index, global_index)
            else:
                # Update the end index to the current global index
                start_index, _ = global_index_ranges[frame_index]
                global_index_ranges[frame_index] = (start_index, global_index)

            global_index += 1

    # Step 2: Build the mapping of frames indices and update their references in relations and descriptions
    # Example: 1st frame has index ranges [0, 3] (4 subframes), update name Frame 0 -> Frames 0-3
    mapping = {}
    relations = []
    descriptions = []

    for frame_index, global_index_range in global_index_ranges.items():
        start, end = global_index_range
        ref_name = f"Frame {start}" if start == end else f"Frames {start}-{end}"
        mapping[frame_index] = ref_name

    for idx1, frame in enumerate(frames):
        for idx2, desc in frame.relations.items():
            desc = desc.replace(f"Frame {idx1}", mapping[idx1])
            desc = desc.replace(f"Frame {idx2}", mapping.get(idx2, "None"))
            relations.append(f"{mapping[idx1]} and {mapping.get(idx2, "None")}: {desc}")

        descriptions.append(f"{mapping[idx1]}: {frame.description}")

    assert len(images) == len(image_captions)

    return all_frames, images, image_captions, descriptions, relations, interactables


Frame.set_frame_as.__doc__ = "\n".join(f"{frame.name}: {frame.description}" for frame in InteractableFrame)

Element.set_element_as.__doc__ = "\n".join(f"{element.name}: {element.description}" for element in InteractableElement)