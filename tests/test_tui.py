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
    assert "Active Aztec Rank" in out
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


def test_session_state_record_cost():
    state = SessionState()
    assert "$0.00" in state.prompt_text()
    state.record_cost(0.19, 3400)
    assert state.total_cost_usd == 0.19
    assert state.total_tokens == 3400
    assert "$0.19" in state.prompt_text()


@pytest.mark.asyncio
async def test_cmd_edit_records_cost_in_session_state(tmp_path):
    from aztec_circle.tui.commands import cmd_edit
    from aztec_circle.engine.patch_agent import PatchResult
    from aztec_circle.engine.project_runner import CommandResult

    console = Console()
    state = SessionState(output_dir=str(tmp_path))
    assert state.total_cost_usd == 0.0

    mock_patch_result = PatchResult(
        success=True,
        edit_summary="Added feature",
        round1_tokens=500,
        round2_tokens=2500,
        total_cost_usd=0.05,
    )

    with patch("aztec_circle.engine.patch_agent.PatchAgent.run", new_callable=AsyncMock) as mock_run, \
         patch("aztec_circle.engine.project_runner.ProjectRunner.typecheck_project", new_callable=AsyncMock) as mock_tc:
        mock_run.return_value = mock_patch_result
        mock_tc.return_value = CommandResult(success=True, stdout="", stderr="", exit_code=0, duration_seconds=0.1)

        await cmd_edit("Add a feature", state, console)

    assert state.total_cost_usd == 0.05
    assert state.total_tokens == 3000
    assert "$0.05" in state.prompt_text()


@pytest.mark.asyncio
async def test_cmd_fix_records_cost_in_session_state(tmp_path):
    from aztec_circle.tui.commands import cmd_fix
    from aztec_circle.engine.build_fixer import FixResult
    from aztec_circle.engine.project_runner import CommandResult

    console = Console()
    state = SessionState(output_dir=str(tmp_path))
    assert state.total_cost_usd == 0.0

    mock_cmd_res = CommandResult(success=True, stdout="", stderr="", exit_code=0, duration_seconds=0.2)
    mock_fix_result = FixResult(
        success=True,
        iterations=1,
        final_build_result=mock_cmd_res,
        patches_applied=["src/App.tsx"],
        total_cost_usd=0.072,
    )

    with patch("aztec_circle.engine.project_runner.ProjectRunner.build_project", new_callable=AsyncMock) as mock_build, \
         patch("aztec_circle.engine.build_fixer.BuildFixAgent.fix", new_callable=AsyncMock) as mock_fix:
        mock_build.return_value = CommandResult(success=False, stdout="", stderr="Error", exit_code=1, duration_seconds=0.2)
        mock_fix.return_value = mock_fix_result

        await cmd_fix("", state, console)

    assert state.total_cost_usd == 0.072
    assert "$0.07" in state.prompt_text()


@pytest.mark.asyncio
async def test_start_interactive_session_initializes_cleanly():
    from aztec_circle.tui.interactive import start_interactive_session

    with patch("prompt_toolkit.PromptSession.prompt_async", side_effect=EOFError), \
         patch("aztec_circle.tui.renderer.print_welcome_banner"):
        await start_interactive_session()


@pytest.mark.asyncio
async def test_cmd_logs_reads_server_log_file(tmp_path):
    from aztec_circle.tui.commands import cmd_logs

    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    log_file = tmp_path / ".aztec_server.log"
    log_file.write_text("Line 1: Server ready on port 5173\nLine 2: HMR update App.tsx\n", encoding="utf-8")

    await cmd_logs("", state, console)
    out = console.export_text()
    assert "Server ready on port 5173" in out
    assert "HMR update App.tsx" in out



