import re
import inspect

import halligan.prompts as Prompts
from halligan.agents import Agent
from halligan.utils.layout import Frame
from halligan.utils.constants import Stage
from halligan.utils.logger import Trace


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

    # Request script from agent
    images = [frame.image for frame in frames]
    image_captions = [f"Frame {i}" for i in range(len(frames))]
    response, _ = agent(prompt, images, image_captions)
    script = get_script(response)
    print(script)

    # Execute response script
    exec(script, tools, {})
    agent.reset()
    return task_objective