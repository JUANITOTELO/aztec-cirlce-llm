"""
Unit tests for multi-tier test runner, port freeing, and dual-service orchestration.
"""

import asyncio
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, patch

from aztec_circle.engine.project_runner import (
    ProjectRunner,
    CommandResult,
    is_port_available,
    find_free_port,
    free_ports,
)


def test_find_free_port_and_availability():
    free_p = find_free_port(5190)
    assert free_p >= 5190
    assert is_port_available(free_p)


def test_free_ports_safe_execution():
    # Calling free_ports on an arbitrary unallocated port should return empty without throwing
    res = free_ports([5999])
    assert isinstance(res, list)


@pytest.mark.asyncio
async def test_test_project_multi_tier_php_and_node():
    runner = ProjectRunner()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Create PHP test script
        backend_dir = os.path.join(tmpdir, "backend")
        os.makedirs(backend_dir, exist_ok=True)
        php_test = os.path.join(backend_dir, "test_backend.php")
        with open(php_test, "w") as f:
            f.write("<?php echo 'PHP backend tests passed'; exit(0);")

        # 2. Mock run_command_streamed to simulate successful test executions
        async def mock_run_cmd(cmd, cwd, title=""):
            if "php" in cmd:
                return CommandResult(success=True, stdout="PHP Backend OK", stderr="", exit_code=0, duration_seconds=0.1)
            elif "npm" in cmd:
                return CommandResult(success=True, stdout="Node Tests OK", stderr="", exit_code=0, duration_seconds=0.2)
            return CommandResult(success=True, stdout="OK", stderr="", exit_code=0, duration_seconds=0.1)

        with patch.object(runner, "run_command_streamed", side_effect=mock_run_cmd):
            res = await runner.test_project(tmpdir)
            assert res.success is True
            assert "PHP Backend OK" in res.stdout


@pytest.mark.asyncio
async def test_tui_clean_command():
    from aztec_circle.tui.session import SessionState
    from aztec_circle.tui.commands import dispatch_slash_command
    from rich.console import Console

    state = SessionState()
    console = Console(record=True)

    handled = await dispatch_slash_command("/clean", state, console)
    assert handled is True
    output = console.export_text()
    assert "Freed" in output or "No lingering" in output
