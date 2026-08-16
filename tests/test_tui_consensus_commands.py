"""
Unit tests for TUI consensus and living roadmap slash commands.
"""

import pytest
from unittest.mock import AsyncMock, patch
from rich.console import Console

from aztec_circle.engine.plan_manager import PlanManager
from aztec_circle.tui.commands import (
    dispatch_slash_command,
    cmd_consensus,
    cmd_plan,
    cmd_roadmap,
)
from aztec_circle.tui.session import SessionState


@pytest.mark.asyncio
async def test_cmd_consensus_dispatch(tmp_path):
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    with patch("aztec_circle.tui.interactive.run_modular_consensus_session", new=AsyncMock(return_value=True)) as mock_run:
        handled = await dispatch_slash_command("/consensus Create a product catalog module", state, console)
        assert handled is True
        mock_run.assert_awaited_once_with("Create a product catalog module", state, console)


@pytest.mark.asyncio
async def test_cmd_module_and_feature_aliases(tmp_path):
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    with patch("aztec_circle.tui.interactive.run_modular_consensus_session", new=AsyncMock(return_value=True)) as mock_run:
        h1 = await dispatch_slash_command("/module Add inventory analytics", state, console)
        assert h1 is True

        h2 = await dispatch_slash_command("/feature Add payment processing", state, console)
        assert h2 is True

        assert mock_run.await_count == 2


@pytest.mark.asyncio
async def test_cmd_plan_with_goal_triggers_consensus(tmp_path):
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    with patch("aztec_circle.tui.interactive.run_modular_consensus_session", new=AsyncMock(return_value=True)) as mock_run:
        handled = await dispatch_slash_command(
            "/plan We would like to create a new module that manages the products in a production ready and holistic way.",
            state,
            console,
        )
        assert handled is True
        mock_run.assert_awaited_once_with(
            "We would like to create a new module that manages the products in a production ready and holistic way.",
            state,
            console,
        )


@pytest.mark.asyncio
async def test_cmd_plan_and_roadmap_dashboard(tmp_path):
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    # Initialize a plan file
    plan_path = PlanManager.sync_from_codebase(str(tmp_path), goal="Test Project")

    # /plan with no args
    handled_plan = await dispatch_slash_command("/plan", state, console)
    assert handled_plan is True
    out1 = console.export_text()
    assert "Living Project Blueprint" in out1 or "Progress" in out1

    # /roadmap
    console_rm = Console(record=True)
    handled_rm = await dispatch_slash_command("/roadmap", state, console_rm)
    assert handled_rm is True
    out2 = console_rm.export_text()
    assert "Living Project Blueprint" in out2 or "Roadmap" in out2
