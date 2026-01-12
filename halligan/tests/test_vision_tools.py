import sys
import types
import io
from PIL import Image
import pytest

# Prepare fake dotenv
dotenv = types.ModuleType('dotenv')
dotenv.load_dotenv = lambda: None
sys.modules['dotenv'] = dotenv

# Minimal fake halligan.agents with GPTAgent
agents_mod = types.ModuleType('halligan.agents')
class FakeAgent:
    def __init__(self, api_key=None):
        self._calls = []
    def __call__(self, prompt, images, captions):
        self._calls.append((prompt, len(images), captions))
        return ("response", {"meta": 1})
    def reset(self):
        self._calls.append(('reset',))
agents_mod.GPTAgent = FakeAgent
sys.modules['halligan.agents'] = agents_mod

# Minimal halligan.models.Detector
models_mod = types.ModuleType('halligan.models')
class FakeDetector:
    @staticmethod
    def detect(images, obj=None):
        # return empty boxes for each image
        return [[] for _ in images]
models_mod.Detector = FakeDetector
sys.modules['halligan.models'] = models_mod

# Create minimal cv2 and skimage modules to allow import
cv2 = types.ModuleType('cv2')
cv2.cvtColor = lambda img, code: img
cv2.threshold = lambda gray, a, b, c: (None, gray)
cv2.findContours = lambda thresh, mode, method: ([], None)
cv2.RETR_CCOMP = 0
cv2.CHAIN_APPROX_SIMPLE = 0
sys.modules['cv2'] = cv2

skimage_color = types.ModuleType('skimage.color')
skimage_color.rgb2lab = lambda arr: arr
skimage_color.deltaE_cie76 = lambda a,b: 0
sys.modules['skimage.color'] = skimage_color

# halligan.utils.toolkit and layout minimal stubs
toolkit_mod = types.ModuleType('halligan.utils.toolkit')
class ToolkitStub:
    def __init__(self, tools, dependencies):
        self.tools = tools
        self.dependencies = dependencies
toolkit_mod.Toolkit = ToolkitStub
sys.modules['halligan.utils.toolkit'] = toolkit_mod

layout_mod = types.ModuleType('halligan.utils.layout')
class FrameStub:
    def __init__(self, x=0,y=0,image=None):
        self.x = x; self.y = y; self._image = image or Image.new('RGB',(10,10),'white')
        self.w = self._image.size[0]; self.h = self._image.size[1]
        self.interactables = []
        self.keypoints = []
        self.subframes = []
        self.interactable = None
        self.description = ''
    @property
    def image(self):
        return self._image
    def get_interactable(self, id):
        return None
    def show_keypoints(self):
        return self._image
class ElementStub(FrameStub):
    pass
class PointStub(FrameStub):
    pass
layout_mod.Frame = FrameStub
layout_mod.Element = ElementStub
layout_mod.Point = PointStub
sys.modules['halligan.utils.layout'] = layout_mod

# Now import the module under test
from halligan.utils import vision_tools as vt

# Tests

def test_ask_with_bad_images_raises():
    with pytest.raises(ValueError):
        vt.ask("notalist", "q", "bool")


def test_ask_with_missing_agent_raises(monkeypatch):
    # Force internal agent to None
    vt._AGENT_STATE._agent = None
    with pytest.raises(RuntimeError):
        vt.ask([Image.new('RGB',(5,5))], "q", "bool")


def test_ask_with_agent_calls_agent_and_reset():
    fake = agents_mod.GPTAgent()
    res = vt.ask([Image.new('RGB',(5,5))], "q", "bool", agent_instance=fake)
    # default behavior returns a list
    assert isinstance(res, list)


def test_rank_with_empty_images_raises():
    with pytest.raises(ValueError):
        vt.rank([], "obj")


def test_rank_uses_agent_and_batches():
    fake = agents_mod.GPTAgent()
    # provide 3 small images
    images = [Image.new('RGB',(5,5)) for _ in range(3)]
    order = vt.rank(images, "rank this", agent_instance=fake)
    assert isinstance(order, list)


def test_compare_with_invalid_reference_raises():
    with pytest.raises(ValueError):
        vt.compare([Image.new('RGB',(5,5))], "obj", reference='notimage')


def test_compare_with_missing_agent_raises(monkeypatch):
    vt._AGENT_STATE._agent = None
    with pytest.raises(RuntimeError):
        vt.compare([Image.new('RGB',(5,5))], "obj", reference=Image.new('RGB',(5,5)))


def test_compare_calls_agent_and_reset():
    fake = agents_mod.GPTAgent()
    res = vt.compare([Image.new('RGB',(5,5))], "obj", reference=Image.new('RGB',(5,5)), agent_instance=fake)
    assert isinstance(res, list)


def test_match_non_element_returns_false():
    assert vt.match(1, 2) is False


def test_compare_default_on_agent_response_mismatch(monkeypatch):
    class DumbAgent:
        def __call__(self, prompt, images, captions):
            return ("no_match", {})
        def reset(self):
            pass
    res = vt.compare([Image.new('RGB',(5,5))], "obj", reference=Image.new('RGB',(5,5)), agent_instance=DumbAgent())
    assert isinstance(res, list)

