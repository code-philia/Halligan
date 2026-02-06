import re
import ast
import time
import logging
from typing import List, Callable
from textwrap import indent

import halligan.prompts as Prompts
from halligan.agents import Agent
from halligan.utils.toolkit import Toolkit
from halligan.utils.constants import Stage
from halligan.utils.layout import Frame, Element, get_observation
from halligan.utils.logger import Trace

logger = logging.getLogger(__name__)


# Stage-specific exceptions (kept local for stage files)
class StageError(Exception):
    pass

class NetworkError(StageError):
    pass

class ToolInvokeError(StageError):
    pass

class ScriptSyntaxError(StageError):
    pass

def _is_network_error(exc: Exception) -> bool:
    return isinstance(exc, (ConnectionError, TimeoutError)) or "network" in str(exc).lower()


def _run_with_retry(func: Callable, retries: int = 3, backoff: float = 0.5):
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as e:
            last_exc = e
            if _is_network_error(e):
                logger.warning(f"Network error attempt {attempt}/{retries}: {e}")
            else:
                logger.warning(f"Error attempt {attempt}/{retries}: {e}")
            if attempt == retries:
                break
            time.sleep(backoff * attempt)

    if last_exc and _is_network_error(last_exc):
        raise NetworkError(str(last_exc)) from last_exc
    if isinstance(last_exc, SyntaxError):
        raise ScriptSyntaxError(str(last_exc)) from last_exc
    raise ToolInvokeError(str(last_exc)) from last_exc


stage = Stage.STRUCTURE_ABSTRACTION


toolkit = Toolkit(
    tools=[
        Frame.get_element,
        Frame.split,
        Frame.grid,
        Frame.set_frame_as,
        Element.set_element_as
    ],
    dependencies={
        **globals(),
        "List": List,
        "__builtins__": __builtins__, 
    }
)


@Trace.section("Structure Abstraction")
def structure_abstraction(agent: Agent, frames: list[Frame], objective: str) -> None: 
    """
    Instruct the agent to annotate interactable Frames and Elements. 
    Frames can be further divided into subframes.
    The agent can segment specific Elements or extract a grid of evenly-sized Elements from Frames.
    
    Returns:
        None: all annotations are stored in the Frame instances (e.g., Frame.interactables).
    """
    def get_script(response: str) -> list[str]:
        pattern = r"```python(.*?)```"
        blocks = re.findall(pattern, response, re.DOTALL)
        code = "\n".join(blocks)
    
        result = ""
        node = ast.parse(code)
        for elem in node.body:
            if isinstance(elem, ast.FunctionDef) and elem.name == "structure_abstraction":
                result = ast.unparse(elem)
                result = result.replace("structure_abstraction", "process")
                break
            
        return result
    
    # Prepare prompt
    _, images, image_captions, descriptions, relations, _ = get_observation(frames)
    prompt = Prompts.get(
        stage=stage,
        descriptions="\n".join(descriptions),
        relations="\n".join(relations),
        objective=objective,
        tool_docs=indent("\n\n".join([tool.docs for tool in toolkit.tools]), "\t"),
    )
    print(prompt)

    # Request script from agent with retries
    def request_script():
        resp = agent(prompt, images, image_captions)
        if isinstance(resp, (tuple, list)):
            resp_text = resp[0]
        else:
            resp_text = resp
        code = get_script(resp_text)
        if not code:
            raise ToolInvokeError("Agent returned no python code block for structure_abstraction")
        return code

    script = _run_with_retry(request_script, retries=3, backoff=0.6)
    print(script)

    # Execute response script safely
    def exec_script():
        try:
            ast.parse(script)
        except SyntaxError as e:
            raise ScriptSyntaxError(str(e)) from e

        env = {}
        try:
            exec(script, toolkit.dependencies, env)
        except Exception as e:
            raise ToolInvokeError(str(e)) from e

        if "process" not in env or not callable(env["process"]):
            raise ToolInvokeError("Agent script did not define a callable 'process(frames)'")

        env["process"](frames)
        return True

    _run_with_retry(exec_script, retries=2, backoff=0.4)
    agent.reset()