"""
Unit tests for Aztec self-updater engine, CLI update commands, and version flags.
"""

import subprocess
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typer.testing import CliRunner
from rich.console import Console

import aztec_circle
from aztec_circle.cli import app
from aztec_circle.engine.updater import AztecUpdater, UpdateCheckResult, UpdateExecutionResult
from aztec_circle.tui.commands import cmd_update
from aztec_circle.tui.session import SessionState

runner = CliRunner()


def test_updater_initialization_and_version():
    updater = AztecUpdater()
    assert updater.current_version == aztec_circle.__version__
    assert updater.current_version == "0.3.0"


def test_updater_find_git_root(tmp_path):
    updater = AztecUpdater()
    root = updater.find_git_root()
    # In current workspace repo, .git exists
    assert root is not None
    assert "aztec-cirlce-llm" in root or ".aztec" in root


def test_updater_check_for_updates_clean():
    updater = AztecUpdater()
    with patch("subprocess.run") as mock_subproc:
        # Mock git fetch and git rev-list
        mock_fetch = MagicMock(returncode=0)
        mock_revlist = MagicMock(returncode=0, stdout="0\n")
        mock_subproc.side_effect = [mock_fetch, mock_revlist]

        result: UpdateCheckResult = updater.check_for_updates()
        assert result.has_update is False
        assert result.commits_behind == 0
        assert "up to date" in result.message


def test_updater_check_for_updates_behind():
    updater = AztecUpdater()
    with patch("subprocess.run") as mock_subproc:
        mock_fetch = MagicMock(returncode=0)
        mock_revlist = MagicMock(returncode=0, stdout="3\n")
        mock_subproc.side_effect = [mock_fetch, mock_revlist]

        result: UpdateCheckResult = updater.check_for_updates()
        assert result.has_update is True
        assert result.commits_behind == 3
        assert "3 new commit(s)" in result.message


def test_updater_check_for_updates_non_git():
    updater = AztecUpdater()
    with patch.object(updater, "find_git_root", return_value=None):
        result: UpdateCheckResult = updater.check_for_updates()
        assert result.has_update is False
        assert "not detected" in result.message


@pytest.mark.asyncio
async def test_updater_perform_update_git_success():
    updater = AztecUpdater()
    mock_pull_proc = MagicMock()
    mock_pull_proc.communicate = AsyncMock(return_value=(b"Already up to date.", b""))
    mock_pull_proc.returncode = 0

    mock_pip_proc = MagicMock()
    mock_pip_proc.communicate = AsyncMock(return_value=(b"Successfully installed", b""))
    mock_pip_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", side_effect=[mock_pull_proc, mock_pip_proc]):
        res: UpdateExecutionResult = await updater.perform_update()
        assert res.success is True
        assert "Successfully updated" in res.message


@pytest.mark.asyncio
async def test_updater_perform_update_no_git_fails():
    updater = AztecUpdater()
    with patch.object(updater, "find_git_root", return_value=None):
        res: UpdateExecutionResult = await updater.perform_update()
        assert res.success is False
        assert "Git repository root not found" in res.message


def test_cli_version_flag():
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "Aztec Decision Circle" in res.stdout
    assert "v0.3.0" in res.stdout


def test_cli_update_check_command():
    with patch("aztec_circle.engine.updater.AztecUpdater.check_for_updates") as mock_check:
        mock_check.return_value = UpdateCheckResult(
            has_update=False,
            current_version="0.3.0",
            latest_version="0.3.0",
            commits_behind=0,
            message="Aztec is up to date.",
        )
        res = runner.invoke(app, ["update", "--check"])
        assert res.exit_code == 0
        assert "Aztec is up to date" in res.stdout


@pytest.mark.asyncio
async def test_tui_update_slash_command():
    state = SessionState()
    console = Console(record=True)
    with patch("aztec_circle.engine.updater.AztecUpdater.check_for_updates") as mock_check:
        mock_check.return_value = UpdateCheckResult(
            has_update=False,
            current_version="0.2.0",
            latest_version="0.2.0",
            commits_behind=0,
            message="Aztec is up to date.",
        )
        await cmd_update("--check", state, console)
        output = console.export_text()
        assert "Aztec is up to date" in output
