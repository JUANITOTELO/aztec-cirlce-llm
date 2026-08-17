"""
Unit tests for interactive TUI console slash commands and confirmation dialogs.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from rich.console import Console

from aztec_circle.domain.models import ConsoleCommand
from aztec_circle.engine.build_fixer import FixResult
from aztec_circle.engine.project_runner import CommandResult
from aztec_circle.tui.commands import (
    dispatch_slash_command,
    cmd_run,
    cmd_php,
    cmd_mysql,
    cmd_sqlite,
)
from aztec_circle.tui.interactive import prompt_confirm_console_command
from aztec_circle.tui.session import SessionState


@pytest.mark.asyncio
async def test_cmd_run_execution(tmp_path):
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    handled = await dispatch_slash_command("/run echo 'tui test'", state, console)
    assert handled is True
    out = console.export_text()
    assert "tui test" in out or "Console Command" in out


@pytest.mark.asyncio
async def test_cmd_sh_and_exec_aliases(tmp_path):
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    handled1 = await dispatch_slash_command("/sh echo 'sh alias'", state, console)
    assert handled1 is True

    handled2 = await dispatch_slash_command("/exec echo 'exec alias'", state, console)
    assert handled2 is True


@pytest.mark.asyncio
async def test_cmd_php_execution(tmp_path):
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    handled = await dispatch_slash_command("/php -r \"echo 'php test output';\"", state, console)
    assert handled is True
    out = console.export_text()
    assert "PHP Execution" in out


@pytest.mark.asyncio
async def test_cmd_sqlite_execution(tmp_path):
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    # Test creating and querying a table in a temporary sqlite db
    db_file = tmp_path / "test.sqlite"
    cmd_str = f"/sqlite {db_file.name} \"CREATE TABLE users(id INT, name TEXT); INSERT INTO users VALUES(1, 'Alice'); SELECT * FROM users;\""

    handled = await dispatch_slash_command(cmd_str, state, console)
    assert handled is True
    out = console.export_text()
    assert "SQLite Execution" in out


@pytest.mark.asyncio
async def test_prompt_confirm_console_command_yes():
    console = Console()
    cmd = ConsoleCommand(command="php migrate.php", description="Database migration")

    with patch("prompt_toolkit.PromptSession.prompt_async", new=AsyncMock(return_value="y")):
        confirmed, edited = await prompt_confirm_console_command(cmd, console, "/tmp")
        assert confirmed is True
        assert edited is None


@pytest.mark.asyncio
async def test_prompt_confirm_console_command_no():
    console = Console()
    cmd = ConsoleCommand(command="php migrate.php", description="Database migration")

    with patch("prompt_toolkit.PromptSession.prompt_async", new=AsyncMock(return_value="n")):
        confirmed, edited = await prompt_confirm_console_command(cmd, console, "/tmp")
        assert confirmed is False
        assert edited is None


@pytest.mark.asyncio
async def test_prompt_confirm_console_command_edit():
    console = Console()
    cmd = ConsoleCommand(command="php migrate.php", description="Database migration")

    with patch("prompt_toolkit.PromptSession.prompt_async", new=AsyncMock(side_effect=["e", "php migrate.php --seed"])):
        confirmed, edited = await prompt_confirm_console_command(cmd, console, "/tmp")
        assert confirmed is True
        assert edited == "php migrate.php --seed"


@pytest.mark.asyncio
async def test_cmd_budget(tmp_path):
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path), budget_limit_usd=1.00)

    # View current budget
    handled1 = await dispatch_slash_command("/budget", state, console)
    assert handled1 is True
    assert "$1.00" in console.export_text()

    # Update budget
    console2 = Console(record=True)
    handled2 = await dispatch_slash_command("/budget 3.50", state, console2)
    assert handled2 is True
    assert state.budget_limit_usd == 3.50
    assert "$3.50" in console2.export_text()


@pytest.mark.asyncio
async def test_cmd_fix_execution_clean(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    with patch("aztec_circle.engine.project_runner.ProjectRunner.verify_project_smart", new_callable=AsyncMock) as mock_vfy:
        mock_vfy.return_value = CommandResult(success=True, stdout="clean", stderr="", exit_code=0, duration_seconds=0.1)
        handled = await dispatch_slash_command("/fix", state, console)
        assert handled is True
        out = console.export_text()
        assert "cleanly with zero errors" in out


@pytest.mark.asyncio
async def test_cmd_fix_execution_with_repair(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    fail_res = CommandResult(success=False, stdout="", stderr="[plugin:vite:react-babel] error", exit_code=1, duration_seconds=0.1)
    with patch("aztec_circle.engine.project_runner.ProjectRunner.verify_project_smart", new_callable=AsyncMock, return_value=fail_res), \
         patch("aztec_circle.engine.build_fixer.BuildFixAgent.fix", new_callable=AsyncMock) as mock_fix:
        mock_fix.return_value = FixResult(success=True, iterations=1, final_build_result=CommandResult(success=True, stdout="", stderr="", exit_code=0, duration_seconds=0.1), patches_applied=["src/App.tsx"], total_cost_usd=0.01)
        handled = await dispatch_slash_command("/fix", state, console)
        assert handled is True
        out = console.export_text()
        assert "Successfully repaired" in out
