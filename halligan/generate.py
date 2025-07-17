import os
import sys
import logging
import traceback
import importlib.util
from io import BytesIO
from textwrap import indent
from datetime import datetime

from PIL import Image
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page

import halligan.utils.action_tools as action_tools
import halligan.utils.examples as Examples
import halligan.prompts as Prompts

from samples import SAMPLES
from halligan.agents import GPTAgent
from halligan.utils.logger import Trace
from halligan.agents import Agent
from halligan.utils.constants import Stage, InteractableElement
from halligan.utils.action_tools import action_toolkits
from halligan.utils.vision_tools import vision_toolkits
from halligan.utils.layout import Frame, get_observation, get_frames
from halligan.stages.stage1 import objective_identification
from halligan.stages.stage2 import structure_abstraction


# Setup logging
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(f"agent-{timestamp}.log")
file_handler.setFormatter(formatter)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Load environment variables
BASE_PATH = os.path.abspath(os.path.dirname(__file__))

load_dotenv()

CACHE_PATH = os.path.join(BASE_PATH, "cache")
BROWSER_URL = os.getenv("BROWSER_URL")
BENCHMARK_URL = os.getenv("BENCHMARK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def prepare_captcha(captcha_type: str, page: Page):
    """
    For the recaptchav2, hcaptcha, and arkose CAPTCHA types,
    an initial prompt or verification screen (such as a "click to begin" button) appears before the main challenge.
    This preliminary step is automatically bypassed, and is not included in the evaluation.
    """
    if "recaptchav2" in captcha_type:
        checkbox = page.frame_locator("#checkbox")
        checkbox.locator("#recaptcha-anchor").click()
        page.wait_for_timeout(2000)
    elif "hcaptcha" in captcha_type:
        checkbox = page.frame_locator("#checkbox")
        checkbox.locator("#anchor").click()
        page.wait_for_timeout(2000)
    elif "arkose" in captcha_type:
        frame = page.frame_locator("#funcaptcha")
        frame.locator(".start-button").click()
    elif "mtcaptcha" in captcha_type:
        page.wait_for_timeout(2000)


@Trace.section("Solution Composition")
def solution_composition(agent: Agent, frames: list[Frame], objective: str) -> None: 
    """
    Agent composes a Python executable solution using vision and action tools.
    """
    examples = []
    dependencies = {}
    action_tool_docs, vision_tool_docs = {}, {}
    _, images, image_captions, descriptions, relations, interactable_types = get_observation(frames)
    
    for interactable_type in interactable_types:
        # Prepare action and vision tools based on interactables
        for (toolkits, docs) in [(action_toolkits, action_tool_docs), (vision_toolkits, vision_tool_docs)]:
            toolkit = toolkits.get(interactable_type)
            if toolkit:
                docs.update({
                    f"{tool.owner}.{tool.name}" if tool.owner else tool.name: tool.docs 
                    for tool in toolkit.tools
                })
                dependencies.update(toolkit.dependencies)

        # Prepare in-context learning examples
        if interactable_type == InteractableElement.NEXT.name: continue
        else: examples.append(Examples.get(interactable_type))

    # Prepare prompt
    prompt = Prompts.get(
        stage=Stage.SOLUTION_COMPOSITION,
        descriptions="\n".join(descriptions),
        relations="\n".join(relations),
        objective=objective,
        examples="\n\n".join(examples),
        action_tools=indent("\n\n".join(action_tool_docs.values()), "\t"),
        vision_tools=indent("\n\n".join(vision_tool_docs.values()), "\t")
    )

    # Request script from agent 
    agent(prompt, images, image_captions)
    agent.reset()

    
def generate_script(captcha_type: str, id: int, region: dict):
    # Load agent
    agent = GPTAgent(api_key=OPENAI_API_KEY)

    # Load generated solution script from cache
    cache_file = os.path.join(CACHE_PATH, f"{captcha_type.replace("/", "_")}.py")
    spec = importlib.util.spec_from_file_location("cache", cache_file)
    cache = importlib.util.module_from_spec(spec)
    sys.modules[captcha_type] = cache
    spec.loader.exec_module(cache)

    with sync_playwright() as p:
        browser = p.chromium.connect(BROWSER_URL)
        context = browser.new_context(viewport={"width": 1344, "height": 768})
        page = context.new_page()

        try:
            url = f"{BENCHMARK_URL}/{captcha_type}/{id}"
            page.goto(url)
            prepare_captcha(url, page)

            # Initialize CAPTCHA solving tools
            action_tools.set_page(page)

            x, y = region["x"], region["y"]
            captcha = Image.open(BytesIO(page.screenshot(clip=region)))
    
            trace_path = os.path.join("results", "generate", f"{captcha_type.replace("/", "_")}.ipynb")
            Trace.start(captcha, trace_path)

            frames = get_frames(x, y, captcha)
            objective = objective_identification(agent, frames)
            logger.info("\t[Stage 1] Objective Identification")
            structure_abstraction(agent, frames, objective)
            logger.info("\t[Stage 2] Structure Abstraction")
            solution_composition(agent, frames, objective)
            logger.info("\t[Stage 3] Solution Composition")
            
        except Exception as e:
            logger.error(f"Error: {e}")
            logger.error(traceback.format_exc())

        finally:
            Trace.stop()
            if not page.is_closed(): page.close()
            context.close()
            browser.close()


for i, (captcha_type, sample_info) in enumerate(SAMPLES.items()):
    logger.info(f"Generating script for CAPTCHA ({i+1} out of {len(SAMPLES)}): {captcha_type}")

    sample_id = sample_info["id"]
    sample_region = sample_info["region"]
    sample_x = sample_region["x"]
    sample_y = sample_region["y"]
    generate_script(captcha_type, sample_id, sample_region)