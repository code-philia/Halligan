# Halligan

Halligan is a generalized visual CAPTCHA solver part of the paper "Visual CAPTCHAs Are Not Safe: Visual-Language Models Can Become Generalized Solvers".

> We show that by abstracting visual CAPTCHAs into a representation that visual language model (VLM) agents can *understand* and *manipulate*, and framing it as a combinatorial search problem, VLM agents are capable of solving any visual CAPTCHA.

- ✅ Halligan does not require browser automation libraries like Selenium, Puppeteer, or Playwright.
- ✅ Halligan works on any screen (mobile, desktop, smart TV) as long as the viewport coordinates are provided.
- ✅ Halligan operates solely at the visual level, without parsing DOM, HTML, or other structured layout data.

## Structure

The repository is organized as follows:
- `/agents`: Creates instances of VLM `Agent`. Send a request containing an instruction prompt, images, and image captions to receive a response from the agent. Currently, it uses `GPT4o`, but it can be extended to support additional services and local models.
- `/models`: Manages instances of large vision models (LVM) for tasks like object detection and image segmentation. Currently supports `GroundingDINO`, `FastSAM`, and `CLIP`. These models are used for component extraction during CAPTCHA metamodel construction and are wrapped as vision tools during the solution composition stage.
- `/prompt`: Contains prompt templates used for objective identification, structure abstraction, and the solution composition stage.
- `/stages`: Implements the objective identification, structure abstraction, and solution composition stage.
- `/utils`: 
    - `/examples`: Provides documented examples for using each tool for in-context learning.
    - `vision_tools.py`: Implements vision tools (mark, focus, compare, rank, match, ask).
    - `action_tools.py`: Implements action tools (type, swap, click, slide, drag).
    - `layout.py`: Defines the CAPTCHA metamodel and component extraction system.
    - `logger.py`: A logging module that generates visualized execution traces, which are stored as .ipynb notebooks.
    - `toolkit.py`: Manages tools and automatically converts them into API documentation to be included in the agent's input prompt.
    - `constants.py`: Defines all valid interactable elements.
