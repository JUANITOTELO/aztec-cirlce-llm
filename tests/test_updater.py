"""
Unit tests for Aztec self-updater engine (safe update semantics), CLI update
commands, version flags, and the new help/runs/stop commands.
"""

import pytest
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch
from typer.testing import CliRunner
from rich.console import Console

import aztec_circle
from aztec_circle.cli import app
from aztec_circle.engine.updater import AztecUpdater, UpdateCheckResult, UpdateExecutionResult
from aztec_circle.tui.commands import cmd_update
from aztec_circle.tui.session import SessionState

runner = CliRunner()


def make_result(**kwargs: Any) -> UpdateCheckResult:
    defaults: Dict[str, Any] = dict(
        has_update=False,
        current_version="0.4.0",
        latest_version="0.4.0",
        commits_behind=0,
        local_commits=0,
        branch="main",
        message="Aztec is up to date.",
    )
    defaults.update(kwargs)
    return UpdateCheckResult(**defaults)


def make_exec(success: bool = True, message: str = "", **kwargs: Any) -> UpdateExecutionResult:
    defaults: Dict[str, Any] = dict(
        old_version="0.4.0",
        new_version="0.4.0",
        message=message,
    )
    defaults.update(kwargs)
    return UpdateExecutionResult(success=success, **defaults)


# ── Engine basics ────────────────────────────────────────────────────────────

def test_updater_initialization_and_version():
    updater = AztecUpdater()
    assert updater.current_version == aztec_circle.__version__
    assert updater.current_version == "0.4.0"


def test_updater_find_git_root(tmp_path):
    updater = AztecUpdater()
    root = updater.find_git_root()
    # In current workspace repo, .git exists
    assert root is not None
    assert "aztec-cirlce-llm" in root or ".aztec" in root


def test_updater_check_for_updates_clean():
    updater = AztecUpdater()
    with patch.object(updater, "_run_sync") as mock_sync:
        mock_sync.side_effect = [
            (0, "main", ""),   # rev-parse branch
            (0, "", ""),       # fetch
            (0, "0", ""),      # behind count
            (0, "2", ""),      # local ahead count
        ]
        result = updater.check_for_updates()
        assert result.has_update is False
        assert result.commits_behind == 0
        assert result.local_commits == 2
        assert "up to date" in result.message


def test_updater_check_for_updates_behind():
    updater = AztecUpdater()
    with patch.object(updater, "_run_sync") as mock_sync:
        mock_sync.side_effect = [
            (0, "main", ""),
            (0, "", ""),
            (0, "3", ""),
            (0, "0", ""),
        ]
        result = updater.check_for_updates()
        assert result.has_update is True
        assert result.commits_behind == 3
        assert "origin/main" in result.message


def test_updater_check_uses_current_branch_not_hardcoded_main():
    updater = AztecUpdater()
    with patch.object(updater, "_run_sync") as mock_sync:
        mock_sync.side_effect = [
            (0, "master", ""),  # branch detection honored
            (0, "", ""),
            (0, "1", ""),
            (0, "0", ""),
        ]
        result = updater.check_for_updates()
        assert result.branch == "master"
        # Fetch targeted origin/master
        fetch_call = mock_sync.call_args_list[1]
        assert "master" in fetch_call.args[1:]


def test_updater_check_for_updates_non_git():
    updater = AztecUpdater()
    with patch.object(updater, "find_git_root", return_value=None):
        result = updater.check_for_updates()
        assert result.has_update is False
        assert "not detected" in result.message


def test_fresh_version_reader_falls_back_to_module_version():
    updater = AztecUpdater()
    assert updater._fresh_installed_version() == aztec_circle.__version__


# ── Safe update semantics ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_perform_update_already_up_to_date_exits_without_git_ops(tmp_path):
    updater = AztecUpdater()
    with patch.object(updater, "find_git_root", return_value=str(tmp_path)), \
         patch.object(updater, "has_dirty_worktree", return_value=False), \
         patch.object(updater, "check_for_updates", return_value=make_result()), \
         patch("asyncio.create_subprocess_exec") as mock_proc:
        res = await updater.perform_update()
        assert res.success is True
        assert "already up to date" in res.message.lower()
        mock_proc.assert_not_called()


@pytest.mark.asyncio
async def test_perform_update_dirty_worktree_refused(tmp_path):
    updater = AztecUpdater()
    with patch.object(updater, "find_git_root", return_value=str(tmp_path)), \
         patch.object(updater, "has_dirty_worktree", return_value=True), \
         patch("asyncio.create_subprocess_exec") as mock_proc:
        res = await updater.perform_update()
        assert res.success is False
        assert "uncommitted changes" in res.message
        mock_proc.assert_not_called()


@pytest.mark.asyncio
async def test_perform_update_fast_forward_success(tmp_path):
    updater = AztecUpdater()

    pull_proc = MagicMock(returncode=0)
    pull_proc.communicate = AsyncMock(return_value=(b"Fast-forward", b""))
    pip_proc = MagicMock(returncode=0)
    pip_proc.communicate = AsyncMock(return_value=(b"", b""))

    with patch.object(updater, "find_git_root", return_value=str(tmp_path)), \
         patch.object(updater, "has_dirty_worktree", return_value=False), \
         patch.object(updater, "check_for_updates", return_value=make_result(has_update=True, commits_behind=3)), \
         patch("asyncio.create_subprocess_exec", side_effect=[pull_proc, pip_proc]) as mock_create:
        res = await updater.perform_update()
        assert res.success is True
        assert "Successfully updated" in res.message
        first_args = mock_create.call_args_list[0].args
        assert "--ff-only" in first_args  # safe fast-forward, never blind rebase


@pytest.mark.asyncio
async def test_perform_update_diverged_refuses_without_force(tmp_path):
    updater = AztecUpdater()
    with patch.object(updater, "find_git_root", return_value=str(tmp_path)), \
         patch.object(updater, "has_dirty_worktree", return_value=False), \
         patch.object(updater, "check_for_updates",
                      return_value=make_result(has_update=True, commits_behind=2, local_commits=5)), \
         patch("asyncio.create_subprocess_exec") as mock_proc:
        res = await updater.perform_update(force=False)
        assert res.success is False
        assert "diverge" in res.message.lower()
        assert "--force" in res.message or "force" in res.message.lower()
        mock_proc.assert_not_called()


@pytest.mark.asyncio
async def test_perform_update_force_rebases_explicitly(tmp_path):
    updater = AztecUpdater()

    pull_proc = MagicMock(returncode=0)
    pull_proc.communicate = AsyncMock(return_value=(b"Rebased", b""))
    pip_proc = MagicMock(returncode=0)
    pip_proc.communicate = AsyncMock(return_value=(b"", b""))

    with patch.object(updater, "find_git_root", return_value=str(tmp_path)), \
         patch.object(updater, "has_dirty_worktree", return_value=False), \
         patch.object(updater, "check_for_updates",
                      return_value=make_result(has_update=True, commits_behind=2, local_commits=5)), \
         patch("asyncio.create_subprocess_exec", side_effect=[pull_proc, pip_proc]) as mock_create:
        res = await updater.perform_update(force=True)
        assert res.success is True
        first_args = mock_create.call_args_list[0].args
        assert "--rebase" in first_args


@pytest.mark.asyncio
async def test_perform_update_pull_failure_surfaces_error(tmp_path):
    updater = AztecUpdater()

    fail_proc = MagicMock(returncode=128)
    fail_proc.communicate = AsyncMock(return_value=(b"", b"conflict: cannot fast-forward"))

    with patch.object(updater, "find_git_root", return_value=str(tmp_path)), \
         patch.object(updater, "has_dirty_worktree", return_value=False), \
         patch.object(updater, "check_for_updates", return_value=make_result(has_update=True, commits_behind=4)), \
         patch("asyncio.create_subprocess_exec", side_effect=[fail_proc]):
        res = await updater.perform_update()
        assert res.success is False
        assert "fast-forward" in res.message or "Git pull failed" in res.message


@pytest.mark.asyncio
async def test_perform_update_no_git_fails():
    updater = AztecUpdater()
    with patch.object(updater, "find_git_root", return_value=None):
        res = await updater.perform_update()
        assert res.success is False
        assert "Git repository root not found" in res.message


# ── CLI ──────────────────────────────────────────────────────────────────────

def test_cli_version_flag():
    res = runner.invoke(app, ["--version"])
    assert res.exit_code == 0
    assert "Aztec Decision Circle" in res.stdout
    assert f"v{aztec_circle.__version__}" in res.stdout


def test_cli_help_command_exists():
    res = runner.invoke(app, ["help"])
    assert res.exit_code == 0
    assert "Usage:" in res.stdout


def test_cli_runs_alias_lists_runs():
    with patch("aztec_circle.cli.CheckpointStore") as mock_store_cls:
        instance = MagicMock()
        instance.list_runs = AsyncMock(return_value=[])
        mock_store_cls.return_value = instance
        res = runner.invoke(app, ["runs"])
        assert res.exit_code == 0
        assert "No runs found" in res.stdout


def test_cli_stop_reports_idle_servers():
    with patch("aztec_circle.engine.project_runner.free_ports", return_value=[]):
        res = runner.invoke(app, ["stop"])
        assert res.exit_code == 0
        assert "No background development servers running" in res.stdout


def test_cli_stop_frees_ports():
    with patch("aztec_circle.engine.project_runner.free_ports", return_value=[5173, 8000]) as mock_free:
        res = runner.invoke(app, ["stop"])
        assert res.exit_code == 0
        assert "5173" in res.stdout
        called_ports = mock_free.call_args.args[0]
        assert 5173 in called_ports and 8015 in called_ports


def test_cli_update_check_command():
    with patch("aztec_circle.engine.updater.AztecUpdater.check_for_updates") as mock_check:
        mock_check.return_value = make_result(message="Aztec is up to date.")
        res = runner.invoke(app, ["update", "--check"])
        assert res.exit_code == 0
        assert "Aztec is up to date" in res.stdout


# ── TUI ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tui_update_slash_command_check():
    state = SessionState()
    console = Console(record=True)
    with patch("aztec_circle.engine.updater.AztecUpdater.check_for_updates") as mock_check:
        mock_check.return_value = make_result(current_version="0.2.0", latest_version="0.2.0")
        await cmd_update("--check", state, console)
        assert "Aztec is up to date" in console.export_text()


@pytest.mark.asyncio
async def test_tui_update_apply_path_no_longer_silent():
    """Regression: /update (apply) used to be a silent no-op."""
    state = SessionState()
    console = Console(record=True)
    with patch("aztec_circle.engine.updater.AztecUpdater.perform_update",
               new=AsyncMock(return_value=make_exec(True, "Successfully updated Aztec to 0.5.0."))):
        await cmd_update("", state, console)
        text = console.export_text()
        assert len(text.strip()) > 0, "/update must produce output"
        assert "Successfully updated" in text


@pytest.mark.asyncio
async def test_tui_update_apply_failure_prints_diagnostic():
    state = SessionState()
    console = Console(record=True)
    with patch("aztec_circle.engine.updater.AztecUpdater.perform_update",
               new=AsyncMock(return_value=make_exec(False, "Git pull failed: network down"))):
        await cmd_update("", state, console)
        text = console.export_text()
        assert "Update failed" in text
        assert "network down" in text


@pytest.mark.asyncio
async def test_tui_update_apply_already_up_to_date_message():
    state = SessionState()
    console = Console(record=True)
    with patch("aztec_circle.engine.updater.AztecUpdater.perform_update",
               new=AsyncMock(return_value=make_exec(True, "Aztec is already up to date."))):
        await cmd_update("-f", state, console)
        text = console.export_text()
        assert "already up to date" in text.lower()
