import re
import ast
from textwrap import indent

import halligan.prompts as Prompts
import halligan.utils.examples as Examples
from halligan.agents import Agent
from halligan.utils.logger import Trace
from halligan.utils.constants import Stage
from halligan.utils.constants import InteractableElement
from halligan.utils.action_tools import action_toolkits
from halligan.utils.vision_tools import vision_toolkits
from halligan.utils.layout import Frame, get_observation


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

    # Request script from agent 
    try:
        response, _ = agent(prompt, images, image_captions)
        script = get_script(response)
        print(script)
        execute_script(script, dependencies)

    except Exception as e:
        feedback = e

        for _ in range(3):
            try:
                print(feedback)
                response, _ = agent(f"Your code has errors, please fix it.\n{feedback}")
                script = get_script(response)
                print(script)
                execute_script(script, dependencies)
                break

            except Exception as e:
                feedback = e

    agent.reset()