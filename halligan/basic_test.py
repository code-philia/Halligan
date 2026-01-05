import os
from difflib import SequenceMatcher
from urllib import error as urllib_error
from urllib import request as urllib_request

import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from samples import SAMPLES

# Load environment variables
load_dotenv()
BROWSER_URL = os.getenv("BROWSER_URL")
BENCHMARK_URL = os.getenv("BENCHMARK_URL")
BENCHMARK_HTTP_URL = os.getenv("BENCHMARK_HTTP_URL", BENCHMARK_URL)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def test_smoke_samples():
    """
    Lightweight unit smoke test that does not require external services.
    Ensures `SAMPLES` is well-formed so the unit-test job always runs ≥1 test.
    """
    assert isinstance(SAMPLES, dict) and len(SAMPLES) > 0
    for name, data in SAMPLES.items():
        assert isinstance(name, str) and name
        assert isinstance(data, dict) and "id" in data


@pytest.mark.integration
def test_browser():
    """
    Verify that a connection can be successfully established to a
    containerized Playwright browser via its WebSocket endpoint.
    """
    if not BROWSER_URL:
        pytest.skip("BROWSER_URL is not set; skipping browser connectivity test.")

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect(BROWSER_URL)
            assert browser is not None, "Could not create Browser instance."
            browser.close()
        except Exception as e:
            pytest.fail(f"Could not connect to browser: {e}")


@pytest.mark.integration
def test_benchmark():
    """
    Verify that the containerized Playwright browser can access and load
    the benchmark application successfully.
    """
    if not BROWSER_URL or not BENCHMARK_URL:
        pytest.skip("BROWSER_URL/BENCHMARK_URL not set; skipping benchmark test.")
    with sync_playwright() as p:
        browser = p.chromium.connect(BROWSER_URL)
        context = browser.new_context(viewport={"width": 1344, "height": 768})
        page = context.new_page()
        response = page.goto(f"{BENCHMARK_URL}/health")

        assert response is not None, "No response received"
        assert response.status == 200, f"Unexpected status code: {response.status}"
        json_data = response.json()
        assert json_data.get("status") == "ok", f"Unexpected JSON response: {json_data}"

        browser.close()


test_captcha_params = [(name, data["id"]) for name, data in SAMPLES.items()]


@pytest.mark.integration
def test_captcha_endpoints_http():
    """Ensure each CAPTCHA endpoint responds with HTTP 200 before UI checks."""

    if not BENCHMARK_HTTP_URL:
        pytest.skip("BENCHMARK_HTTP_URL not set; skipping endpoint availability check.")

    failures: list[str] = []
    for captcha, data in SAMPLES.items():
        sample_id = data["id"]
        url = f"{BENCHMARK_HTTP_URL}/{captcha}/{sample_id}"
        try:
            with urllib_request.urlopen(url, timeout=15) as resp:
                status = resp.getcode()
        except urllib_error.HTTPError as err:
            status = err.code
            snippet = err.read().decode("utf-8", "ignore")[:200]
            failures.append(f"{captcha}/{sample_id} -> {status}: {snippet}")
            continue
        except urllib_error.URLError as err:
            pytest.fail(f"Failed to reach {url}: {err}")

        if status != 200:
            failures.append(f"{captcha}/{sample_id} -> {status}")

    if failures:
        pytest.fail("\n".join(failures))


@pytest.mark.integration
@pytest.mark.parametrize("captcha, sample_id", test_captcha_params)
def test_captchas(captcha, sample_id):
    """
    Verify that all CAPTCHA samples in the benchmark can be accessed and
    loaded successfully.

    The benchmark includes 26 different types of CAPTCHAs, each served via
    a distinct endpoint. This test ensures that each endpoint is reachable
    and returns the expected content.
    """
    if not BROWSER_URL or not BENCHMARK_URL:
        pytest.skip("BROWSER_URL/BENCHMARK_URL not set; skipping CAPTCHA tests.")
    with sync_playwright() as p:
        browser = p.chromium.connect(BROWSER_URL)
        try:
            context = browser.new_context(viewport={"width": 1344, "height": 768})
            page = context.new_page()
            response = page.goto(f"{BENCHMARK_URL}/{captcha}/{sample_id}")
            if response is None or response.status != 200:
                pytest.skip(
                    f"Endpoint not available for {captcha}/{sample_id}: status={getattr(response, 'status', None)}"
                )

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

            assert (
                SequenceMatcher(
                    None,
                    "\n".join(full_snapshot),
                    open(f"./snapshots/{captcha.replace("/", "_")}.txt").read(),
                ).ratio()
                > 0.5
            )
        finally:
            try:
                browser.close()
            except Exception:
                pass


@pytest.mark.integration
def test_models_initialize_integration():
    """
    Verify that Halligan's additional models (CLIP, FastSAM, DINOv2) can be initialized.

    Note: GPTAgent construction is covered by a unit test (does not require network).
    """
    try:
        from halligan.models import CLIP, Detector, Segmenter
    except Exception:
        pytest.skip("halligan.models components (CLIP/Segmenter/Detector) are not available; skipping.")

    clip = CLIP()
    assert clip is not None, "Failed to initialize CLIP"

    segmenter = Segmenter()
    assert segmenter is not None, "Failed to initialize Segmenter (FastSAM)"

    detector = Detector()
    assert detector is not None, "Failed to initialize Detector (DINOv2)"
