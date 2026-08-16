"""
Tests for Aztec Interactive Terminal UI (TUI), slash commands, and completer.
"""

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch
from prompt_toolkit.document import Document
from rich.console import Console

from aztec_circle.config import settings
from aztec_circle.domain.models import FallbackPolicy
from aztec_circle.engine.checkpoint import CheckpointStore
from aztec_circle.tui.completer import SlashCompleter
from aztec_circle.tui.commands import (
    dispatch_slash_command,
    cmd_help,
    cmd_status,
    cmd_models,
    cmd_policy,
    cmd_runs,
    cmd_resume,
    cmd_clear,
)
from aztec_circle.tui.session import SessionState
from aztec_circle.tui.renderer import TranscriptRenderer, print_welcome_banner


def test_slash_completer_suggestions():
    completer = SlashCompleter()
    doc = Document("/h", cursor_position=2)
    completions = list(completer.get_completions(doc, None))
    assert len(completions) >= 1
    assert any(c.text == "/help" for c in completions)

    doc_all = Document("/", cursor_position=1)
    completions_all = list(completer.get_completions(doc_all, None))
    assert len(completions_all) >= 8


def test_session_state_recording():
    state = SessionState(budget_limit_usd=2.0)
    assert "$0.00" in state.prompt_text()

    state.record_run(cost_usd=0.154, tokens=4500, loops=1, task_id="test-task-123")
    assert state.total_cost_usd == 0.154
    assert state.total_tokens == 4500
    assert state.loop_count == 1
    assert state.active_task_id == "test-task-123"
    assert "$0.15" in state.prompt_text()


@pytest.mark.asyncio
async def test_dispatch_slash_help():
    console = Console(record=True)
    state = SessionState()
    handled = await dispatch_slash_command("/help", state, console)
    assert handled is True
    out = console.export_text()
    assert "Aztec Interactive TUI Commands" in out
    assert "/help" in out
    assert "/status" in out


@pytest.mark.asyncio
async def test_dispatch_slash_status():
    console = Console(record=True)
    state = SessionState(total_cost_usd=0.45, total_tokens=12000)
    handled = await dispatch_slash_command("/status", state, console)
    assert handled is True
    out = console.export_text()
    assert "Aztec Session Status" in out
    assert "$0.4500" in out
    assert "12,000" in out


@pytest.mark.asyncio
async def test_dispatch_slash_models():
    console = Console(record=True)
    state = SessionState()
    handled = await dispatch_slash_command("/models", state, console)
    assert handled is True
    out = console.export_text()
    assert "Aztec Agent Model Assignments" in out
    assert "Youth" in out
    assert "Peer" in out
    assert "Elder" in out

    # Test updating a model
    handled_update = await dispatch_slash_command("/models PEER gemini/gemini-2.5-pro", state, console)
    assert handled_update is True
    assert settings.PEER_MODEL == "gemini/gemini-2.5-pro"


@pytest.mark.asyncio
async def test_dispatch_slash_policy():
    console = Console(record=True)
    state = SessionState()
    handled = await dispatch_slash_command("/policy", state, console)
    assert handled is True
    out = console.export_text()
    assert "Current Fallback Policy" in out

    # Test updating policy
    handled_update = await dispatch_slash_command("/policy BEST_EFFORT_RELEASE", state, console)
    assert handled_update is True
    assert state.fallback_policy == FallbackPolicy.BEST_EFFORT_RELEASE


@pytest.mark.asyncio
async def test_dispatch_slash_runs(tmp_path):
    console = Console(record=True)
    state = SessionState()

    db_path = str(tmp_path / "test_runs.db")
    store = CheckpointStore(db_path=db_path)

    with patch("aztec_circle.tui.commands.CheckpointStore", return_value=store):
        handled = await dispatch_slash_command("/runs", state, console)
        assert handled is True
        out = console.export_text()
        assert "No historical runs found" in out


@pytest.mark.asyncio
async def test_dispatch_slash_resume_missing():
    console = Console(record=True)
    state = SessionState()
    handled = await dispatch_slash_command("/resume non_existent_task", state, console)
    assert handled is True
    out = console.export_text()
    assert "No checkpoint found" in out


@pytest.mark.asyncio
async def test_dispatch_slash_clear():
    console = MagicMock()
    state = SessionState()
    handled = await dispatch_slash_command("/clear", state, console)
    assert handled is True
    console.clear.assert_called_once()


@pytest.mark.asyncio
async def test_dispatch_free_text_returns_false():
    console = Console()
    state = SessionState()
    handled = await dispatch_slash_command("Design a distributed lock in Python", state, console)
    assert handled is False


def test_transcript_renderer_deliverable(tmp_path):
    console = Console(record=True)
    renderer = TranscriptRenderer(console)
    output_dir = str(tmp_path / "out")

    deliverable = {
        "deliverable": {
            "architecture_overview": "Test Architecture Overview",
            "mitigations_applied": ["Applied lock striping"],
            "implementation_code": {
                "lock.py": "class DistributedLock:\n    pass\n",
                "src/types/pose.ts": "export interface Pose { x: number; y: number; }\n",
                "frontend/components/App.tsx": "export const App = () => <div>App</div>;\n"
            }
        }
    }

    renderer.render_deliverable(deliverable, output_dir=output_dir)
    out = console.export_text()
    assert "Aztec Circle Deliverable Summary" in out
    assert "Test Architecture Overview" in out
    assert "Applied lock striping" in out
    assert os.path.exists(os.path.join(output_dir, "lock.py"))
    assert os.path.exists(os.path.join(output_dir, "src/types/pose.ts"))
    assert os.path.exists(os.path.join(output_dir, "frontend/components/App.tsx"))


def test_print_welcome_banner():
    console = Console(record=True)
    state = SessionState()
    print_welcome_banner(console, state)
    out = console.export_text()
    assert "AZTEC" in out or "Multi-Generational" in out
