import re
import ast
import time
import logging
from textwrap import indent
from typing import Callable

import halligan.prompts as Prompts
import halligan.utils.examples as Examples
from halligan.agents import Agent
from halligan.utils.logger import Trace
from halligan.utils.constants import Stage
from halligan.utils.constants import InteractableElement
from halligan.utils.action_tools import action_toolkits
from halligan.utils.vision_tools import vision_toolkits
from halligan.utils.layout import Frame, get_observation

logger = logging.getLogger(__name__)


# local stage exceptions
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


stage = Stage.SOLUTION_COMPOSITION


@Trace.section("Solution Composition")
def solution_composition(agent: Agent, frames: list[Frame], objective: str) -> None: 
    """
    Agent composes a Python executable solution using vision and action tools.
    """
    def get_script(response: str) -> list[str]:
        pattern = r"```python(.*?)```"
        blocks = re.findall(pattern, response, re.DOTALL)
        code = "\n".join(blocks)
    
        result = ""
        node = ast.parse(code)
        for elem in node.body:
            if isinstance(elem, ast.FunctionDef) and elem.name == "solve":
                result = ast.unparse(elem)
                break
            
        return result
    
    def execute_script(script: str, dependencies: dict):
        if "==" in script:
            raise ValueError("Exact match (==) is illegal, you must find the closest, best possible answer.")
        
        if "get_keypoint" in script and "get_neighbour" not in script:
            raise ValueError("You must narrow down the keypoint search space with get_neighbour()")
        
        env = {}
        exec(script, dependencies, env)
        env["solve"](all_frames)
    
    examples = []
    dependencies = {}
    action_tool_docs, vision_tool_docs = {}, {}
    all_frames, images, image_captions, descriptions, relations, interactable_types = get_observation(frames)
    
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
        stage=stage,
        descriptions="\n".join(descriptions),
        relations="\n".join(relations),
        objective=objective,
        examples="\n\n".join(examples),
        action_tools=indent("\n\n".join(action_tool_docs.values()), "\t"),
        vision_tools=indent("\n\n".join(vision_tool_docs.values()), "\t")
    )
    print(prompt)

    # Request script from agent (retries on network errors)
    def request_script():
        resp = agent(prompt, images, image_captions)
        if isinstance(resp, (tuple, list)):
            resp_text = resp[0]
        else:
            resp_text = resp
        script = get_script(resp_text)
        if not script:
            raise ToolInvokeError("Agent returned no python script block")
        return script

    try:
        script = _run_with_retry(request_script, retries=3, backoff=0.6)
        print(script)

        # try executing; if execution fails due to code errors, ask agent to fix
        try:
            # validate syntax
            ast.parse(script)
        except SyntaxError as e:
            raise ScriptSyntaxError(str(e)) from e

        try:
            execute_script(script, dependencies)
        except Exception as e:
            feedback = e
            # ask agent to fix up to 3 times
            for attempt in range(1, 4):
                logger.info(f"Asking agent to fix code (attempt {attempt}/3): {feedback}")
                def request_fix():
                    resp = agent(f"Your code has errors, please fix it.\n{feedback}", images, image_captions)
                    if isinstance(resp, (tuple, list)):
                        return resp[0]
                    return resp

                fixed_resp = _run_with_retry(request_fix, retries=2, backoff=0.5)
                fixed_script = get_script(fixed_resp)
                if not fixed_script:
                    feedback = ToolInvokeError("Agent did not return a python script when asked to fix code")
                    continue

                try:
                    ast.parse(fixed_script)
                except SyntaxError as e:
                    feedback = ScriptSyntaxError(str(e))
                    continue

                try:
                    execute_script(fixed_script, dependencies)
                    script = fixed_script
                    break
                except Exception as e:
                    feedback = e
                    continue
            else:
                # attempted fixes exhausted
                raise ToolInvokeError(f"Agent failed to produce a working script: {feedback}") from feedback

    finally:
        try:
            agent.reset()
        except Exception:
            logger.debug("Failed to reset agent after solution_composition")