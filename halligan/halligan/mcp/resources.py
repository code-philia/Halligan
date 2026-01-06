from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from halligan.mcp.errors import MCPInvalidParams, MCPResourceNotFound
from halligan.mcp.policy import MCPPolicy
from halligan.runtime.config import RuntimeConfig
from halligan.runtime.registry import ToolRegistry
from halligan.utils import examples as Examples
from halligan.utils.layout import Frame, get_observation

ResourceReader = Callable[[], Any]


@dataclass(frozen=True)
class Resource:
    uri: str
    description: str
    read: ResourceReader


class ResourceStore:
    """
    A minimal resource registry (Context-as-Resource).

    Resources are intentionally read-only: they should *expose* context, not
    mutate execution state.
    """

    def __init__(self, resources: list[Resource], *, policy: MCPPolicy | None = None) -> None:
        self._resources = {r.uri: r for r in resources}
        self._policy = policy or MCPPolicy()

    def list(self) -> list[dict[str, str]]:
        return [{"uri": r.uri, "description": r.description} for r in self._resources.values()]

    def read(self, uri: str) -> Any:
        if not isinstance(uri, str) or not uri:
            raise MCPInvalidParams("uri must be a non-empty string")
        self._policy.check_resource_uri(uri)
        res = self._resources.get(uri)
        if not res:
            raise MCPResourceNotFound(uri)
        value = res.read()
        return self._policy.clip_resource(value)

    @staticmethod
    def build(
        *,
        frames: list[Frame] | None = None,
        objective: str | None = None,
        config: RuntimeConfig | None = None,
        registry: ToolRegistry | None = None,
        policy: MCPPolicy | None = None,
    ) -> "ResourceStore":
        """
        Build a default resource store for a Halligan run.

        The store is stage-agnostic: callers can pass what they have, and the
        resource list will adapt accordingly.
        """
        policy = policy or MCPPolicy()
        resources: list[Resource] = []

        # --- Config (redacted) ---
        if config is not None:

            def _runtime_config() -> dict[str, Any]:
                # Never expose API keys to the model.
                return {
                    "browser_url": config.browser_url,
                    "benchmark_url": config.benchmark_url,
                    "benchmark_http_url": config.benchmark_http_url,
                    "allow_nonlocal_benchmark": config.allow_nonlocal_benchmark,
                    "allow_nonlocal_browser": config.allow_nonlocal_browser,
                }

            resources.append(Resource("mcp://config/runtime", "Runtime configuration (redacted).", _runtime_config))

        # --- Observation ---
        if frames is not None:
            all_frames, _, _, descriptions, relations, interactables = get_observation(frames)

            resources.append(
                Resource(
                    "mcp://observation/summary",
                    "High-level observation summary (frame count, interactables).",
                    lambda: {
                        "frames": len(frames),
                        "leaf_frames": len(all_frames),
                        "interactable_types": sorted(interactables),
                    },
                )
            )
            resources.append(
                Resource(
                    "mcp://observation/descriptions", "Stage-1 frame descriptions.", lambda: "\n".join(descriptions)
                )
            )
            resources.append(
                Resource("mcp://observation/relations", "Stage-1 frame relations.", lambda: "\n".join(relations))
            )

        # --- Objective ---
        if objective is not None:
            resources.append(
                Resource("mcp://objective", "Task objective (generic, non-answer-revealing).", lambda: objective)
            )

        # --- Tools ---
        if registry is not None:
            resources.append(
                Resource(
                    "mcp://tools/names",
                    "Allowlisted tool names (Stage 3).",
                    lambda: registry.names(),
                )
            )

        # --- Examples ---
        # Expose examples as separate resources to avoid hard-coding large blobs into prompts.
        resources.append(
            Resource(
                "mcp://examples/list",
                "List available in-context examples by interactable type.",
                Examples.list_types,
            )
        )

        def _example_reader(uri: str) -> ResourceReader:
            def _read() -> str:
                # uri: mcp://examples/<TYPE>
                interactable = uri.split("/", maxsplit=3)[-1]
                return Examples.get(interactable)

            return _read

        # Provide a small, conservative set of example URIs.
        for interactable in Examples.list_types():
            uri = f"mcp://examples/{interactable}"
            resources.append(Resource(uri, f"In-context example for {interactable}.", _example_reader(uri)))

        return ResourceStore(resources, policy=policy)
