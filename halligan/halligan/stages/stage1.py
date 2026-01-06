import halligan.prompts as Prompts
from halligan.agents import Agent
from halligan.mcp.client import InProcessMCPClient
from halligan.mcp.policy import MCPPolicy
from halligan.mcp.resources import ResourceStore
from halligan.mcp.server import InProcessMCPServer
from halligan.mcp.session import request_json_with_mcp
from halligan.runtime.errors import ParseError, ValidationError
from halligan.runtime.schemas import validate_stage1
from halligan.utils.constants import Stage
from halligan.utils.layout import Frame
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
    # Prepare prompt + MCP resources (Context-as-Resource).
    # Stage 1 is primarily image-driven, but we keep MCP wiring consistent across
    # all stages so the runtime has a single, auditable interface surface.
    base_prompt = Prompts.get(stage=stage, frames=len(frames))
    prompt = base_prompt
    print(base_prompt)

    policy = MCPPolicy()
    resources = ResourceStore.build(frames=frames, policy=policy)
    mcp = InProcessMCPClient(InProcessMCPServer(resources=resources, policy=policy))

    # Request structured JSON from agent
    images = [frame.image for frame in frames]
    image_captions = [f"Frame {i}" for i in range(len(frames))]
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            data = request_json_with_mcp(
                agent=agent,
                prompt=prompt,
                images=images,
                image_captions=image_captions,
                mcp=mcp,
                stage_name="Stage 1",
            )
            result = validate_stage1(data, frames=len(frames))

            for i, desc in enumerate(result.descriptions):
                frames[i].description = desc

            for rel in result.relations:
                frames[rel.src].relations[rel.dst] = rel.relationship

            agent.reset()
            return result.objective

        except (ParseError, ValidationError, Exception) as exc:
            last_error = exc
            prompt = (
                base_prompt + "\n\n" + "## Previous error\n" + f"{exc}\n\n"
                "Please output ONLY valid JSON that matches the required schema.\n"
                "Do not include markdown fences or any extra text."
            )

    agent.reset()
    raise last_error if last_error else RuntimeError("Stage 1 failed without a captured error")
