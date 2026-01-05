from __future__ import annotations

from dataclasses import dataclass

from halligan.agents import Agent
from halligan.runtime.config import RuntimeConfig


@dataclass(frozen=True)
class RuntimeContext:
    """
    Runtime dependencies that should be injected (not constructed at import-time).
    """

    agent: Agent
    config: RuntimeConfig
