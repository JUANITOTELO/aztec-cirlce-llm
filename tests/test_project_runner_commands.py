"""
Unit tests for ProjectRunner.run_shell_command_streamed.
"""

import pytest
import tempfile
import os
from rich.console import Console
from aztec_circle.engine.project_runner import ProjectRunner, CommandResult


@pytest.mark.asyncio
async def test_run_shell_command_streamed_success(tmp_path):
    console = Console(record=True)
    runner = ProjectRunner(console=console)

    res = await runner.run_shell_command_streamed(
        cmd_str="echo 'hello world'",
        cwd=str(tmp_path),
        title="Test Echo",
    )

    assert res.success is True
    assert res.exit_code == 0
    assert "hello world" in res.stdout
    assert res.duration_seconds >= 0.0


@pytest.mark.asyncio
async def test_run_shell_command_streamed_pipes_and_redirects(tmp_path):
    console = Console(record=True)
    runner = ProjectRunner(console=console)

    # Write a test file
    sql_file = tmp_path / "schema.sql"
    sql_file.write_text("CREATE TABLE users (id INT, role VARCHAR(50));\nINSERT INTO users VALUES (1, 'admin');\n", encoding="utf-8")

    out_file = tmp_path / "output.txt"
    res = await runner.run_shell_command_streamed(
        cmd_str=f"cat schema.sql | grep 'admin' > {out_file.name}",
        cwd=str(tmp_path),
        title="Pipes and Redirects",
    )

    assert res.success is True
    assert res.exit_code == 0
    assert out_file.exists()
    assert "admin" in out_file.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_run_shell_command_streamed_failure(tmp_path):
    console = Console(record=True)
    runner = ProjectRunner(console=console)

    res = await runner.run_shell_command_streamed(
        cmd_str="exit 42",
        cwd=str(tmp_path),
        title="Failing Command",
    )

    assert res.success is False
    assert res.exit_code == 42
