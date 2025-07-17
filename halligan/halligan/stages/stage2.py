import re
import ast
from typing import List
from textwrap import indent

import halligan.prompts as Prompts
from halligan.agents import Agent
from halligan.utils.toolkit import Toolkit
from halligan.utils.constants import Stage
from halligan.utils.layout import Frame, Element, get_observation
from halligan.utils.logger import Trace


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

    # Request script from agent
    response, _ = agent(prompt, images, image_captions)
    script = get_script(response)
    print(script)

    # Execute response script
    env = {}
    exec(script, toolkit.dependencies, env)
    env["process"](frames)
    agent.reset()