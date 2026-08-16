"""
Unit tests for Aztec ConfigManager, credential persistence, TUI config commands, and CLI config options.
"""

import os
import stat
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from typer.testing import CliRunner
from rich.console import Console

from aztec_circle.config import settings
from aztec_circle.engine.config_manager import ConfigManager
from aztec_circle.cli import app
from aztec_circle.tui.commands import cmd_config, cmd_keys, cmd_models, cmd_preset, cmd_test_models
from aztec_circle.tui.session import SessionState

runner = CliRunner()


def test_mask_key():
    assert ConfigManager.mask_key("") == "[dim]Not Set[/dim]"
    assert ConfigManager.mask_key(None) == "[dim]Not Set[/dim]"
    assert ConfigManager.mask_key("short") == "[dim]Not Set[/dim]"
    assert ConfigManager.mask_key("AIzaSyD1234567890") == "AIzaSy...7890"
    assert ConfigManager.mask_key("sk-ant-api03-abcdef123456") == "sk-ant...3456"


def test_config_manager_file_permissions(tmp_path):
    with patch.object(ConfigManager, "get_config_dir", return_value=tmp_path):
        cfg_file = ConfigManager.get_config_file_path()
        assert cfg_file.exists()
        ConfigManager.save_api_key("GEMINI_API_KEY", "AIzaSyFakeKey123456")
        mode = os.stat(cfg_file).st_mode
        # Check owner read/write permissions
        assert mode & stat.S_IRUSR
        assert mode & stat.S_IWUSR
        assert os.environ.get("GEMINI_API_KEY") == "AIzaSyFakeKey123456"


def test_save_model_assignment(tmp_path):
    with patch.object(ConfigManager, "get_config_dir", return_value=tmp_path):
        ConfigManager.save_model_assignment("YOUTH", "gemini/gemini-3.7-flash")
        assert settings.YOUTH_MODEL == "gemini/gemini-3.7-flash"

        ConfigManager.save_model_assignment("PEER", "anthropic/claude-3-7-sonnet-20250219")
        assert settings.PEER_MODEL == "anthropic/claude-3-7-sonnet-20250219"


def test_apply_preset(tmp_path):
    with patch.object(ConfigManager, "get_config_dir", return_value=tmp_path):
        res = ConfigManager.apply_preset("speed_budget")
        assert res is True
        assert settings.YOUTH_MODEL == "gemini/gemini-3.7-flash"
        assert settings.PEER_MODEL == "gemini/gemini-3.7-flash"
        assert settings.ELDER_MODEL == "gemini/gemini-3.7-flash"
        assert settings.FALLBACK_MODEL == "groq/llama-3.3-70b-versatile"

        res_anth = ConfigManager.apply_preset("anthropic_efficiency")
        assert res_anth is True
        assert settings.YOUTH_MODEL == "anthropic/claude-haiku-4-5"
        assert settings.PEER_MODEL == "anthropic/claude-sonnet-5"
        assert settings.ELDER_MODEL == "anthropic/claude-sonnet-5"
        assert settings.FALLBACK_MODEL == "anthropic/claude-haiku-4-5"

        res_budg = ConfigManager.apply_preset("anthropic_budget")
        assert res_budg is True
        assert settings.YOUTH_MODEL == "anthropic/claude-haiku-4-5"
        assert settings.PEER_MODEL == "anthropic/claude-haiku-4-5"
        assert settings.ELDER_MODEL == "anthropic/claude-haiku-4-5"
        assert settings.FALLBACK_MODEL == "anthropic/claude-haiku-4-5"


@pytest.mark.asyncio
async def test_test_model_connection_success():
    with patch("litellm.validate_environment", return_value={"keys_in_environment": True}), \
         patch("litellm.acompletion", new_callable=AsyncMock) as mock_comp:
        mock_comp.return_value = MagicMock()
        success, msg, latency = await ConfigManager.test_model_connection("gemini/gemini-3.7-flash")
        assert success is True
        assert "Connected" in msg
        assert latency >= 0.0


@pytest.mark.asyncio
async def test_test_model_connection_missing_key():
    with patch("litellm.validate_environment", return_value={"keys_in_environment": False, "missing_keys": ["ANTHROPIC_API_KEY"]}):
        success, msg, latency = await ConfigManager.test_model_connection("anthropic/claude-3-7-sonnet-20250219")
        assert success is False
        assert "Missing API key" in msg


@pytest.mark.asyncio
async def test_tui_cmd_keys_and_models(tmp_path):
    console = Console(record=True)
    state = SessionState()

    with patch.object(ConfigManager, "get_config_dir", return_value=tmp_path):
        await cmd_keys("", state, console)
        out = console.export_text()
        assert "GEMINI_API_KEY" in out

        await cmd_models("", state, console)
        out = console.export_text()
        assert "Active Aztec Rank" in out

        await cmd_models("catalog", state, console)
        out = console.export_text()
        assert "Curated Frontier Model Catalog" in out


@pytest.mark.asyncio
async def test_tui_cmd_preset_and_test(tmp_path):
    console = Console(record=True)
    state = SessionState()

    with patch.object(ConfigManager, "get_config_dir", return_value=tmp_path), \
         patch.object(ConfigManager, "test_model_connection", new_callable=AsyncMock, return_value=(True, "Online", 0.15)):
        await cmd_preset("google_suite", state, console)
        assert settings.PEER_MODEL == "gemini/gemini-2.5-pro"

        await cmd_test_models("", state, console)
        out = console.export_text()
        assert "Model Ping Test Results" in out
        assert "Online" in out


def test_cli_config_commands(tmp_path):
    with patch.object(ConfigManager, "get_config_dir", return_value=tmp_path):
        res = runner.invoke(app, ["config", "--set-key", "GROQ_API_KEY=gsk_test123456"])
        assert res.exit_code == 0
        assert "GROQ_API_KEY" in os.environ

        res = runner.invoke(app, ["config", "--set-model", "YOUTH=gemini/gemini-3.7-flash"])
        assert res.exit_code == 0
        assert settings.YOUTH_MODEL == "gemini/gemini-3.7-flash"

        res = runner.invoke(app, ["config", "--preset", "max_reasoning"])
        assert res.exit_code == 0
        assert settings.PEER_MODEL == "anthropic/claude-sonnet-5"

        res = runner.invoke(app, ["config", "--list-models"])
        assert res.exit_code == 0

        res = runner.invoke(app, ["config"])
        assert res.exit_code == 0


@pytest.mark.asyncio
async def test_run_interactive_config_menu_async():
    from aztec_circle.tui.config_ui import run_interactive_config_menu
    console = Console(record=True)
    state = SessionState()

    # Mock session prompt_async to return "3" (browse catalog) then "0" (exit)
    with patch("prompt_toolkit.PromptSession.prompt_async", new_callable=AsyncMock) as mock_prompt:
        mock_prompt.side_effect = ["3", "0"]
        await run_interactive_config_menu(console, state)
        out = console.export_text()
        assert "Aztec Configuration Center" in out
        assert "Curated Frontier Model Catalog" in out

