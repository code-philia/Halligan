import os
from difflib import SequenceMatcher

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from samples import SAMPLES


# Load environment variables
load_dotenv()
BROWSER_URL = os.getenv("BROWSER_URL")
BENCHMARK_URL = os.getenv("BENCHMARK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def test_browser():
    """
    Verify that a connection can be successfully established to a 
    containerized Playwright browser via its WebSocket endpoint.
    """
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect(BROWSER_URL)
            assert browser is not None, "Could not create Browser instance."
            browser.close()
        except Exception as e:
            pytest.fail(f"Could not connect to browser: {e}")


def test_benchmark():
    """
    Verify that the containerized Playwright browser can access and load 
    the benchmark application successfully.
    """
    with sync_playwright() as p:
        browser = p.chromium.connect(BROWSER_URL)
        context = browser.new_context(viewport={"width": 1344, "height": 768})
        page = context.new_page()
        response = page.goto(BENCHMARK_URL)

        assert response is not None, "No response received"
        assert response.status == 500, f"Unexpected status code: {response.status}"
        json_data = response.json()
        assert "message" in json_data, f"Unexpected JSON response: {json_data}"

        browser.close()


test_captcha_params = [(name, data["id"]) for name, data in SAMPLES.items()]

@pytest.mark.parametrize("captcha, sample_id", test_captcha_params)
def test_captchas(captcha, sample_id):
    """
    Verify that all CAPTCHA samples in the benchmark can be accessed and 
    loaded successfully.

    The benchmark includes 26 different types of CAPTCHAs, each served via 
    a distinct endpoint. This test ensures that each endpoint is reachable 
    and returns the expected content.
    """
    with sync_playwright() as p:
        browser = p.chromium.connect(BROWSER_URL)
        context = browser.new_context(viewport={"width": 1344, "height": 768})
        page = context.new_page()
        page.goto(f"{BENCHMARK_URL}/{captcha}/{sample_id}")

        if "recaptchav2" in captcha:
            checkbox = page.frame_locator("#checkbox")
            checkbox.locator("#recaptcha-anchor").click()
            page.wait_for_timeout(2000)
        elif "hcaptcha" in captcha:
            checkbox = page.frame_locator("#checkbox")
            checkbox.locator("#anchor").click()
            page.wait_for_timeout(2000)
        elif "arkose" in captcha:
            frame = page.frame_locator("#funcaptcha")
            frame.locator(".start-button").click()
        elif "mtcaptcha" in captcha:
            page.wait_for_timeout(2000)

        # Get snapshot of main frame
        full_snapshot = [page.locator("body").aria_snapshot()]

        # Get all iframe elements
        iframes = page.locator("iframe")
        iframe_count = iframes.count()

        # Loop through each iframe and collect its ARIA snapshot
        for i in range(iframe_count):
            frame = iframes.nth(i).content_frame
            if frame:
                iframe_snapshot = frame.locator("body").aria_snapshot()
                full_snapshot.append(iframe_snapshot)

        assert SequenceMatcher(None, "\\n".join(full_snapshot), open(f"./snapshots/{captcha.replace("/", "_")}.txt").read()).ratio() > 0.5


def test_halligan():
    """
    Verify that Halligan's VLM agent and all the additional models (CLIP, FastSAM, DINOv2)
    can be successfully initialized.
    """
    from halligan.agents import GPTAgent
    from halligan.models import CLIP, Segmenter, Detector

    agent = GPTAgent(api_key=OPENAI_API_KEY)
    assert agent is not None, "Failed to initialize GPTAgent."
    
    clip = CLIP()
    assert clip is not None, "Failed to initialize CLIP"

    segmenter = Segmenter()
    assert segmenter is not None, "Failed to initialize Segmenter (FastSAM)"

    detector = Detector()
    assert detector is not None, "Failed to initialize Detector (DINOv2)"