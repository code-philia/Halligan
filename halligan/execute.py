import os
import sys
import logging
import traceback
import importlib.util
from io import BytesIO
from datetime import datetime

from PIL import Image
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page

import halligan.utils.action_tools as action_tools
from samples import SAMPLES
from halligan.agents import GPTAgent
from halligan.utils.logger import Trace
from halligan.utils.layout import get_frames, get_observation
from halligan.stages.stage1 import objective_identification
from halligan.stages.stage2 import structure_abstraction
from halligan.stages.stage3 import solution_composition

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


def solve_captcha(captcha_type: str, id: int, region: dict) -> bool:
    # Load agent
    agent = GPTAgent(api_key=OPENAI_API_KEY)

    # Load generated solution script from cache
    cache_file = os.path.join(CACHE_PATH, f"{captcha_type.replace("/", "_")}.py")
    spec = importlib.util.spec_from_file_location("cache", cache_file)
    cache = importlib.util.module_from_spec(spec)
    sys.modules[captcha_type] = cache
    spec.loader.exec_module(cache)

    solved = False
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
    
            trace_path = os.path.join("results", "execute", f"{captcha_type.replace("/", "_")}.ipynb")
            Trace.start(captcha, trace_path)

            @Trace.section("Objective Identification")
            def stage1(frames): return cache.stage1(frames)

            @Trace.section("Structure Abstraction")
            def stage2(frames): return cache.stage2(frames)

            @Trace.section("Solution Composition")
            def stage3(frames): return cache.stage3(frames)

            frames = get_frames(x, y, captcha)

            if cache and hasattr(cache, "stage1"):
                objective = stage1(frames)
            else:
                objective = objective_identification(agent, frames)

            agent.reset()

            if cache and hasattr(cache, "stage2"):
                stage2(frames)
            else:
                structure_abstraction(agent, frames, objective)
            
            agent.reset()

            with page.expect_response(lambda r: "/submit" in r.url, timeout=60000) as response_info:
                if cache and hasattr(cache, "stage3"):
                    frames, _, _, _, _, _ = get_observation(frames)
                    stage3(frames)
                else:
                    solution_composition(agent, frames, objective)
                
            response = response_info.value
            data: dict = response.json()
            solved = data.get("solved", None)

            agent.reset()
            
        except Exception as e:
            logger.error(f"Error: {e}")
            logger.error(traceback.format_exc())

        finally:
            Trace.stop()
            if not page.is_closed(): page.close()
            context.close()
            browser.close()
    
    return solved


for i, (captcha_type, sample_info) in enumerate(SAMPLES.items()):
    logger.info(f"Testing CAPTCHA ({i+1} out of {len(SAMPLES)}): {captcha_type}")

    sample_id = sample_info["id"]
    sample_region = sample_info["region"]
    sample_x = sample_region["x"]
    sample_y = sample_region["y"]
    solved = solve_captcha(captcha_type, sample_id, sample_region)
    logger.info(f"Solved: {solved}")