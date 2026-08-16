"""
Tests for Typer CLI commands, rendering, and lifecycle execution.
"""

from unittest.mock import AsyncMock, patch
import pytest
from typer.testing import CliRunner
from aztec_circle.cli import _render_dashboard, app
from aztec_circle.domain.models import CirclePhase, CircleRunState, FallbackPolicy
from aztec_circle.engine.checkpoint import CheckpointStore

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Aztec Decision Circle" in result.stdout
    assert "run" in result.stdout
    assert "resume" in result.stdout
    assert "list-runs" in result.stdout
    assert "serve" in result.stdout


def test_cli_render_dashboard():
    state = CircleRunState(
        goal="Test rendering goal",
        current_phase=CirclePhase.PEER_DRAFTING,
        loop_count=1,
        total_cost_usd=0.0125,
    )
    last_event = {"event": "peer.drafting", "loop": 1}
    panel = _render_dashboard(state, last_event)
    assert panel is not None


def test_cli_list_runs_empty(temp_db_path):
    with patch("aztec_circle.config.settings.CHECKPOINT_DB_PATH", temp_db_path):
        result = runner.invoke(app, ["list-runs"])
        assert result.exit_code == 0
        assert "No runs found" in result.stdout


def test_cli_list_runs_with_items(temp_db_path):
    async def _seed():
        store = CheckpointStore(db_path=temp_db_path)
        s = CircleRunState(goal="Seeded Goal", current_phase=CirclePhase.RESOLVED)
        await store.save(s)

    import asyncio
    asyncio.run(_seed())

    with patch("aztec_circle.config.settings.CHECKPOINT_DB_PATH", temp_db_path):
        result = runner.invoke(app, ["list-runs"])
        assert result.exit_code == 0
        assert "Seeded Goal" in result.stdout


def test_cli_resume_non_existent_run():
    result = runner.invoke(app, ["resume", "non-existent-task-id-1234"])
    assert result.exit_code != 0
    assert "No checkpoint found" in result.stdout or "Error" in result.stdout


def test_cli_resume_valid_run(temp_db_path):
    state = CircleRunState(goal="Resume Task", current_phase=CirclePhase.RESOLVED)

    async def _seed():
        store = CheckpointStore(db_path=temp_db_path)
        await store.save(state)

    import asyncio
    asyncio.run(_seed())

    mock_run_result = {"status": "APPROVED", "task_id": state.task_id}
    with patch("aztec_circle.config.settings.CHECKPOINT_DB_PATH", temp_db_path), \
         patch("aztec_circle.engine.state_machine.AztecOrchestrator.run", new_callable=AsyncMock) as mock_orch:
        mock_orch.return_value = mock_run_result
        result = runner.invoke(app, ["resume", state.task_id])
        assert result.exit_code == 0
        assert "Resuming task" in result.stdout


def test_cli_run_command(temp_db_path):
    mock_run_result = {"status": "APPROVED", "task_id": "test-task-123"}
    with patch("aztec_circle.config.settings.CHECKPOINT_DB_PATH", temp_db_path), \
         patch("aztec_circle.engine.state_machine.AztecOrchestrator.run", new_callable=AsyncMock) as mock_orch:
        mock_orch.return_value = mock_run_result
        result = runner.invoke(app, ["run", "Build a queue", "--budget", "0.50", "--max-loops", "1"])
        assert result.exit_code == 0
        assert "Initializing Aztec Circle" in result.stdout
