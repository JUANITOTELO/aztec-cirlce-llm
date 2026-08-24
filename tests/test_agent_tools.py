"""
Tests for agent tool access: the bridge (menu / parsing / execution), the
PeerAgent bounded tool loop against a scripted multi-round provider, and
orchestrator wiring of project_root.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from aztec_circle.adapters.llm_provider import LLMResponse
from aztec_circle.agents.peer import PeerAgent
from aztec_circle.domain.models import CircleRunState
from aztec_circle.engine.state_machine import AztecOrchestrator
from aztec_circle.tools import ToolContext, get_registry
from aztec_circle.tools.agent_bridge import (
    build_tool_menu,
    execute_tool_requests,
    parse_tool_requests,
    render_tool_results,
)


@pytest.fixture
def project(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "server.py").write_text("PORT = 8080\n")
    return tmp_path


# ── Bridge units ─────────────────────────────────────────────────────────────

def test_parse_tool_requests_requires_explicit_array():
    assert parse_tool_requests('{"architecture_overview": "x"}') == []
    assert parse_tool_requests("plain prose") == []
    reqs = parse_tool_requests(json.dumps({
        "tool_requests": [
            {"tool": "fs_read", "args": {"path": "src/server.py"}, "reason": "check port"},
            {"bogus": True},          # skipped
        ],
        "implementation_code": {},    # ignored — requests take priority
    }))
    assert len(reqs) == 1 and reqs[0]["tool"] == "fs_read"


def test_build_tool_menu_lists_safety_and_params(project):
    reg = get_registry(str(project))
    menu = build_tool_menu(reg)
    assert "fs_read [read_only]" in menu
    assert "shell_run [dangerous]" in menu


@pytest.mark.asyncio
async def test_mutating_request_denied_without_approver(project):
    reg = get_registry(str(project))
    ctx = ToolContext(project_root=str(project), auto_approve=False)
    results = await execute_tool_requests(
        [{"tool": "fs_write", "args": {"path": "evil.txt", "content": "x"}}], reg, ctx
    )
    assert results[0]["denied"] is True
    assert not (project / "evil.txt").exists()


@pytest.mark.asyncio
async def test_unknown_tool_reported_not_raised(project):
    reg = get_registry(str(project))
    results = await execute_tool_requests([{"tool": "nope"}], reg, make_ctx(project))
    assert results[0]["ok"] is False and "unknown tool" in results[0]["error"]


def make_ctx(project):
    return ToolContext(project_root=str(project), auto_approve=True)


# ── PeerAgent bounded tool loop ──────────────────────────────────────────────

class ScriptedProvider:
    """Returns canned responses in order; records every message list."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls: list = []

    async def complete(self, messages=None, model=None, temperature=0.35, on_chunk=None, **kwargs):
        self.calls.append([dict(m) for m in messages])
        content = self.responses.pop(0)
        return LLMResponse(content=content, prompt_tokens=100, completion_tokens=50, total_tokens=150, model=model or "m")


FINAL_DRAFT = json.dumps({
    "architecture_overview": "Final draft",
    "implementation_code": {"main.py": "print('v2')"},
    "mitigations_applied": [],
    "assumptions_made": [],
})

TOOL_REQUEST_TURN = json.dumps({
    "tool_requests": [{"tool": "fs_read", "args": {"path": "src/server.py"}, "reason": "find port"}],
})


@pytest.mark.asyncio
async def test_peer_agent_full_tool_loop(project):
    provider = ScriptedProvider([TOOL_REQUEST_TURN, FINAL_DRAFT])
    agent = PeerAgent(provider=provider, tool_registry=get_registry(str(project)), project_root=str(project))

    draft = await agent.run(goal="update the server", youth_risks=[])

    # Two LLM rounds happened.
    assert len(provider.calls) == 2
    # The tool protocol was offered in round 1's user message.
    assert "PROJECT TOOL ACCESS" in provider.calls[0][1]["content"]
    # Round 2 contains assistant request + TOOL RESULTS with real file output.
    round2_roles = [m["role"] for m in provider.calls[1]]
    assert round2_roles[-2:] == ["assistant", "user"]
    results_msg = provider.calls[1][-1]["content"]
    assert "TOOL RESULTS" in results_msg and "PORT = 8080" in results_msg
    # Final deliverable parsed from last response.
    assert draft.architecture_overview == "Final draft"
    # Token usage folded across both calls (100+100 prompt).
    assert draft.input_tokens >= 200


@pytest.mark.asyncio
async def test_peer_agent_without_tools_is_single_call(project):
    provider = ScriptedProvider([FINAL_DRAFT])
    agent = PeerAgent(provider=provider)  # no registry/project_root
    draft = await agent.run(goal="g", youth_risks=[])
    assert len(provider.calls) == 1
    assert "PROJECT TOOL ACCESS" not in provider.calls[0][1]["content"]
    assert draft.architecture_overview == "Final draft"


@pytest.mark.asyncio
async def test_peer_agent_tool_budget_exhaustion_takes_last_answer(project):
    always_ask = json.dumps({"tool_requests": [{"tool": "fs_list", "args": {"path": "."}}]})
    provider = ScriptedProvider([always_ask, always_ask, always_ask])  # model never finalizes
    agent = PeerAgent(provider=provider, tool_registry=get_registry(str(project)), project_root=str(project))

    draft = await agent.run(goal="g", youth_risks=[])
    # max_rounds=2 -> at most 3 LLM calls; loop terminates on budget.
    assert len(provider.calls) <= 3
    assert isinstance(draft.architecture_overview, str)


# ── Orchestrator wiring ──────────────────────────────────────────────────────

def test_orchestrator_passes_project_root_to_peer(project):
    from tests.conftest import MockLLMProvider

    orch = AztecOrchestrator(
        state=CircleRunState(goal="g"),
        checkpoint_store=AsyncMock(),
        youth_agents=[MagicStub(), MagicStub()],
        peer_agent=PeerAgent(provider=MockLLMProvider()),
        elder_agents=[MagicStub(), MagicStub()],
        project_root=str(project),
    )
    assert orch.peer_agent.project_root == str(project)
    assert orch.peer_agent.tool_registry is not None
    assert orch.peer_agent.tool_registry.get("fs_read") is not None


def test_orchestrator_without_root_leaves_peer_untouched():
    from tests.conftest import MockLLMProvider

    peer = PeerAgent(provider=MockLLMProvider())
    AztecOrchestrator(
        state=CircleRunState(goal="g"),
        checkpoint_store=AsyncMock(),
        youth_agents=[MagicStub(), MagicStub()],
        peer_agent=peer,
        elder_agents=[MagicStub(), MagicStub()],
    )
    assert peer.tool_registry is None


class MagicStub:
    """Minimal stand-in for rank agents when the run never reaches them."""
    persona = "stub"
    model = "stub-model"
    provider = None
