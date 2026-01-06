from __future__ import annotations

from halligan.agents import GPTAgent


def test_gpt_agent_constructs_without_network():
    # The client is constructed but no network request is performed.
    agent = GPTAgent(api_key="sk-test", model="gpt-4o-2024-11-20")
    assert agent is not None
