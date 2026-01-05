import halligan.prompts as Prompts
from halligan.agents import Agent
from halligan.mcp.client import InProcessMCPClient
from halligan.mcp.policy import MCPPolicy
from halligan.mcp.resources import ResourceStore
from halligan.mcp.server import InProcessMCPServer
from halligan.mcp.session import request_json_with_mcp
from halligan.runtime.errors import ParseError, ToolError, ValidationError
from halligan.runtime.executor import execute_stage3_program
from halligan.runtime.registry import build_default_registry
from halligan.runtime.schemas import validate_stage3
from halligan.utils import vision_tools
from halligan.utils.constants import Stage
from halligan.utils.layout import Frame, get_observation
from halligan.utils.logger import Trace

stage = Stage.SOLUTION_COMPOSITION


@Trace.section("Solution Composition")
def solution_composition(agent: Agent, frames: list[Frame], objective: str) -> None:
    """
    Agent composes a Python executable solution using vision and action tools.
    """
    all_frames, images, image_captions, _, _, interactable_types = get_observation(frames)

    # Tools exposed to the JSON program (functions only).
    # NOTE: Stage 3 program execution may pass non-JSON Python objects (Frame/Element/Point);
    # therefore we keep tool invocation in-process and enforce policy at a single choke point.
    registry = build_default_registry()
    policy = MCPPolicy(allowed_tools=set(registry.names()))
    resources = ResourceStore.build(frames=frames, objective=objective, registry=registry, policy=policy)
    mcp = InProcessMCPClient(InProcessMCPServer(registry=registry, resources=resources, policy=policy))

    # Prepare prompt (short, resource-first).
    interactable_str = ", ".join(sorted(t for t in interactable_types))
    base_prompt = Prompts.get(stage=stage, objective=objective, frames=len(frames), interactable_types=interactable_str)
    prompt = base_prompt
    print(base_prompt)

    # Request JSON program from agent and execute it safely
    feedback: Exception | None = None
    for _ in range(4):
        try:
            data = request_json_with_mcp(
                agent=agent,
                prompt=prompt,
                images=images,
                image_captions=image_captions,
                mcp=mcp,
                stage_name="Stage 3",
                allowed_methods=("resources/read", "resources/list", "tools/list"),
            )
            program = validate_stage3(data)

            # Vision tools require an injected agent instance.
            agent.reset()
            vision_tools.set_agent(agent)
            execute_stage3_program(all_frames, program, registry=registry, invoker=mcp)
            agent.reset()
            return

        except (ParseError, ValidationError, ToolError, Exception) as exc:
            feedback = exc
            prompt = (
                base_prompt
                + "\n\n"
                + "## Previous error\n"
                + f"{exc}\n\n"
                + "Please output ONLY valid JSON that matches the required schema.\n"
                + "Do not include markdown fences or any extra text."
            )

    agent.reset()
    raise feedback if feedback else RuntimeError("Stage 3 failed without a captured error")
