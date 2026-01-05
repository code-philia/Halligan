import halligan.prompts as Prompts
from halligan.agents import Agent
from halligan.mcp.client import InProcessMCPClient
from halligan.mcp.policy import MCPPolicy
from halligan.mcp.resources import ResourceStore
from halligan.mcp.server import InProcessMCPServer
from halligan.mcp.session import request_json_with_mcp
from halligan.runtime.errors import ParseError, ValidationError
from halligan.runtime.executor import apply_stage2_plan
from halligan.runtime.schemas import validate_stage2
from halligan.utils.constants import Stage
from halligan.utils.layout import Frame, get_observation
from halligan.utils.logger import Trace

stage = Stage.STRUCTURE_ABSTRACTION


@Trace.section("Structure Abstraction")
def structure_abstraction(agent: Agent, frames: list[Frame], objective: str) -> None:
    """
    Instruct the agent to annotate interactable Frames and Elements.
    Frames can be further divided into subframes.
    The agent can segment specific Elements or extract a grid of evenly-sized Elements from Frames.

    Returns:
        None: all annotations are stored in the Frame instances (e.g., Frame.interactables).
    """
    # Prepare prompt + MCP context (Context-as-Resource).
    # We keep the primary prompt short and allow the model to pull extra context
    # (descriptions/relations) via read-only MCP resources if needed.
    _, images, image_captions, _, _, _ = get_observation(frames)
    base_prompt = Prompts.get(stage=stage, frames=len(frames), objective=objective)
    prompt = base_prompt
    policy = MCPPolicy()
    resources = ResourceStore.build(frames=frames, objective=objective, policy=policy)
    mcp = InProcessMCPClient(InProcessMCPServer(resources=resources, policy=policy))
    print(base_prompt)

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            data = request_json_with_mcp(
                agent=agent,
                prompt=prompt,
                images=images,
                image_captions=image_captions,
                mcp=mcp,
                stage_name="Stage 2",
            )
            plan = validate_stage2(data, frames=len(frames))
            apply_stage2_plan(frames, plan)
            agent.reset()
            return

        except (ParseError, ValidationError, Exception) as exc:
            last_error = exc
            prompt = (
                base_prompt + "\n\n" + "## Previous error\n" + f"{exc}\n\n"
                "Please output ONLY valid JSON that matches the required schema.\n"
                "Do not include markdown fences or any extra text."
            )

    agent.reset()
    raise last_error if last_error else RuntimeError("Stage 2 failed without a captured error")
