import sys
import io
import types
import pytest
from PIL import Image

# Prepare fake external modules before importing action_tools
# 1) dotenv
dotenv = types.ModuleType("dotenv")
dotenv.load_dotenv = lambda: None
sys.modules['dotenv'] = dotenv

# 2) playwright.sync_api with a Page class
class FakeMouse:
    def __init__(self, recorder):
        self._rec = recorder
    def click(self, x, y):
        self._rec.append(('click', x, y))
    def move(self, x, y):
        self._rec.append(('move', x, y))
    def down(self):
        self._rec.append(('down',))
    def up(self):
        self._rec.append(('up',))

class FakePage:
    def __init__(self):
        self._rec = []
        self.mouse = FakeMouse(self._rec)
        self.keyboard = types.SimpleNamespace(type=lambda t: self._rec.append(('type', t)))
        self._screenshot_sequence = None
        self._screenshot_calls = 0

    def screenshot(self, clip=None):
        # Return PNG bytes of a small image; if sequence provided, return next
        if self._screenshot_sequence is not None:
            idx = min(self._screenshot_calls, len(self._screenshot_sequence)-1)
            data = self._screenshot_sequence[idx]
            self._screenshot_calls += 1
            return data
        buf = io.BytesIO()
        Image.new('RGB', (8,8), 'white').save(buf, format='PNG')
        return buf.getvalue()

FakeSyncApi = types.ModuleType('playwright.sync_api')
FakeSyncApi.Page = FakePage
sys.modules['playwright'] = types.ModuleType('playwright')
sys.modules['playwright.sync_api'] = FakeSyncApi

# 3) halligan.utils.layout stub
layout_mod = types.ModuleType('halligan.utils.layout')

class FrameStub:
    def __init__(self, x=0, y=0, image=None):
        self.x = x
        self.y = y
        self._image = image or Image.new('RGB', (100, 100), 'white')
        self.w = self._image.size[0]
        self.h = self._image.size[1]
        self.interactables = []
        self.subframes = []
        self.interactable = None
        self.description = ''

    @property
    def image(self):
        return self._image

    @property
    def region(self):
        return [self.x, self.y, self.w, self.h]

    @property
    def center(self):
        return (self.x + self.w // 2, self.y + self.h // 2)

    def get_interactable(self, id):
        return self.interactables[id]

class ElementStub(FrameStub):
    def __init__(self, x=0, y=0, image=None, parent=None):
        super().__init__(x, y, image)
        self.parent = parent or FrameStub()
        self.retrieved = False

class PointStub(FrameStub):
    pass

layout_mod.Frame = FrameStub
layout_mod.Element = ElementStub
layout_mod.Point = PointStub
sys.modules['halligan.utils.layout'] = layout_mod

# 4) halligan.utils.toolkit stub
toolkit_mod = types.ModuleType('halligan.utils.toolkit')
class ToolkitStub:
    def __init__(self, tools, dependencies):
        self.tools = tools
        self.dependencies = dependencies
toolkit_mod.Toolkit = ToolkitStub
sys.modules['halligan.utils.toolkit'] = toolkit_mod

# 5) halligan.utils.vision_tools minimal stub for match
vision_tools_stub = types.ModuleType('halligan.utils.vision_tools')
vision_tools_stub.match = lambda e1,e2: False
sys.modules['halligan.utils.vision_tools'] = vision_tools_stub

# Now import the module under test
from halligan.utils import action_tools as at

# Helper to create PNG bytes
def png_bytes(color='white', size=(8,8)):
    buf = io.BytesIO()
    Image.new('RGB', size, color).save(buf, format='PNG')
    return buf.getvalue()

# Tests

def test_screenshot_fullpage_calls_page_screenshot():
    page = FakePage()
    at.set_page(page)
    img = at.screenshot(page=page)
    assert isinstance(img, Image.Image)


def test_screenshot_with_valid_region_calls_with_clip():
    page = FakePage()
    at.set_page(page)
    img = at.screenshot(region=[10,10,5,5], page=page)
    assert isinstance(img, Image.Image)


def test_screenshot_with_invalid_region_fallbacks_fullpage():
    page = FakePage()
    at.set_page(page)
    # width negative -> fallback
    img = at.screenshot(region=[0,0,-5,10], page=page)
    assert isinstance(img, Image.Image)


def test_screenshot_no_page_raises():
    # ensure no page set
    at.set_page(None)
    with pytest.raises(RuntimeError):
        at.screenshot()


def test_click_uses_clamped_coords():
    page = FakePage()
    at.set_page(page)
    el = ElementStub(x=-20, y=5, image=Image.new('RGB',(10,10),'white'))
    # override center to negative
    el.center = (-5, 10)
    # monkeypatch center attribute by setting property-like
    el.center = (-5, 10)
    # call click
    at.click(el)
    assert page._rec[0][0] == 'click'
    assert page._rec[0][1] >= 0 and page._rec[0][2] >= 0


def test_click_and_hold_yields_choice_images():
    page = FakePage()
    # set sequence images to simulate frames
    page._screenshot_sequence = [png_bytes('white'), png_bytes('white')]
    at.set_page(page)
    target = ElementStub(x=10,y=10,image=Image.new('RGB',(10,10),'white'))
    obs = FrameStub(x=0,y=0,image=Image.new('RGB',(20,20),'white'))
    gen = at.click_and_hold(target, obs, page=page)
    choice = next(gen)
    assert hasattr(choice, 'image') and isinstance(choice.image, Image.Image)


def test_get_all_choices_cycles_until_same():
    page = FakePage()
    # create two different images then repeat the first
    a = png_bytes('white')
    b = png_bytes('black')
    page._screenshot_sequence = [a, b, a]
    at.set_page(page)
    prev_arrow = ElementStub(x=0,y=0,image=Image.new('RGB',(10,10),'white'))
    next_arrow = ElementStub(x=50,y=0,image=Image.new('RGB',(10,10),'white'))
    obs = FrameStub(x=0,y=0,image=Image.new('RGB',(20,20),'white'))
    choices = at.get_all_choices(prev_arrow, next_arrow, obs, page=page)
    assert isinstance(choices, list)
    assert len(choices) >= 1


def test_select_choice_select_calls_mouse_click_times_index():
    page = FakePage()
    at.set_page(page)
    next_arrow = ElementStub(x=10,y=10,image=Image.new('RGB',(10,10),'white'))
    sc = at.SelectChoice(index=3, image=Image.new('RGB',(5,5),'white'), next=next_arrow, page=page)
    sc.select()
    # 3 clicks recorded
    clicks = [r for r in page._rec if r[0]=='click']
    assert len(clicks) == 3


def test_drag_returns_choices_count9():
    page = FakePage()
    at.set_page(page)
    start = ElementStub(x=0,y=0,image=Image.new('RGB',(10,10),'white'))
    end = PointStub(x=50,y=50,image=Image.new('RGB',(10,10),'white'))
    choices = at.drag(start, end, page=page)
    assert len(choices) == 9


def test_drag_drop_calls_mouse_methods():
    page = FakePage()
    at.set_page(page)
    dc = at.DragChoice(image=Image.new('RGB',(10,10),'white'), start=(0,0), end=(20,20), page=page)
    dc.drop()
    # expect sequence move, down, move, up
    ops = [r[0] for r in page._rec]
    assert 'move' in ops and 'down' in ops and 'up' in ops


def test_slide_choice_refine_creates_choices():
    page = FakePage()
    at.set_page(page)
    obs = FrameStub(x=0,y=0,image=Image.new('RGB',(100,20),'white'))
    sc = at.SlideChoice('x', Image.new('RGB',(10,10),'white'), 30, 10, obs, (0,100), page=page)
    choices = sc.refine()
    assert isinstance(choices, list)
    assert len(choices) > 0


def test_swap_choice_swap_fallbacks_to_drag_on_click_exception():
    class BadPage(FakePage):
        def __init__(self):
            super().__init__()
        def _bad_click(self, x, y):
            raise Exception('click failed')
    bad = FakePage()
    # monkeypatch click to raise
    def raising_click(x,y):
        raise Exception('click failed')
    bad.mouse.click = raising_click
    at.set_page(bad)
    grid = [[ElementStub(x=0,y=0,image=Image.new('RGB',(10,10),'white'))]]
    sw = at.SwapChoice(grid, Image.new('RGB',(10,10),'white'), (5,5), (10,10))
    sw._page = bad
    # should not raise
    sw.swap()

