import re
import inspect
import time
import logging
from typing import Callable

import halligan.prompts as Prompts
from halligan.agents import Agent
from halligan.utils.layout import Frame
from halligan.utils.constants import Stage
from halligan.utils.logger import Trace

logger = logging.getLogger(__name__)


# Stage-specific exception types
class StageError(Exception):
    pass

class NetworkError(StageError):
    pass

class ToolInvokeError(StageError):
    pass

class ScriptSyntaxError(StageError):
    pass

class FatalStageError(StageError):
    pass


def _is_network_error(exc: Exception) -> bool:
    # heuristic: ConnectionError, TimeoutError or message
    return isinstance(exc, (ConnectionError, TimeoutError)) or "network" in str(exc).lower()


def _run_with_retry(func: Callable, retries: int = 3, backoff: float = 0.5, retry_on=None):
    retry_on = retry_on or (Exception,)
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            return func()
        except Exception as e:
            last_exc = e
            # classify
            if _is_network_error(e):
                logger.warning(f"Network error on attempt {attempt}/{retries}: {e}")
            else:
                logger.warning(f"Error on attempt {attempt}/{retries}: {e}")

            if attempt == retries:
                break
            time.sleep(backoff * attempt)

    # determine proper exception type
    if last_exc and _is_network_error(last_exc):
        raise NetworkError(str(last_exc)) from last_exc
    if isinstance(last_exc, SyntaxError):
        raise ScriptSyntaxError(str(last_exc)) from last_exc
    raise ToolInvokeError(str(last_exc)) from last_exc


stage = Stage.OBJECTIVE_IDENTIFICATION


@Trace.section("Objective Identification")
def objective_identification(agent: Agent, frames: list[Frame]) -> str:
    """
    Ask the agent to give a detailed visual description of each frame.
    Then, identify the relations between frames and infer the overall task objective.

    Updates:
        Frame.description
        Frame.relations
    
    Returns:
        objective (str): The inferred task objective.
    """
    task_objective: str = ""

    def get_script(response: str) -> str:
        pattern = r"```python(.*?)```"
        blocks = re.findall(pattern, response, re.DOTALL)
        return "".join(blocks)
        
    def describe(frame_id: int, description: str):
        frames[frame_id].description = description

    def relate(frame_id1: int, frame_id2: int = None, relationship: str = ""):
        frames[frame_id1].relations[frame_id2] = relationship

    def objective(description: str):
        nonlocal task_objective
        task_objective = description

    # Prepare tools
    tools = {"describe": describe, "relate": relate, "objective": objective}

    # Prepare prompt
    prompt = Prompts.get(
        stage=stage,
        tools="\n".join(
            f"{func.__name__}{inspect.signature(func)}"
            for func in tools.values()
        ),
        frames=len(frames)
    )
    print(prompt)

    # Request script from agent (with retries on network/tool errors)
    images = [frame.image for frame in frames]
    image_captions = [f"Frame {i}" for i in range(len(frames))]

    def request_and_extract():
        resp = agent(prompt, images, image_captions)
        # agent may return (response, metadata)
        if isinstance(resp, tuple) or isinstance(resp, list):
            resp_text = resp[0]
        else:
            resp_text = resp
        script_text = get_script(resp_text)
        if not script_text:
            # ask agent to reformat or raise to trigger retry
            raise ToolInvokeError("Agent returned no python script block")
        return script_text

    script = _run_with_retry(request_and_extract, retries=3, backoff=0.7)
    print(script)

    # Execute response script (parse first to give clear syntax errors)
    def exec_script():
        try:
            # validate syntax first
            import ast
            ast.parse(script)
        except SyntaxError as e:
            # don't retry syntax errors
            raise ScriptSyntaxError(str(e)) from e

        try:
            exec_globals = dict(tools)
            exec(script, exec_globals, {})
        except Exception as e:
            # tool invocation error inside the executed script
            raise ToolInvokeError(str(e)) from e
        return True

    _run_with_retry(exec_script, retries=2, backoff=0.5)
    agent.reset()
    return task_objective