"""
Unit tests for granular role and rank model selection, resolution hierarchy, and TUI/CLI commands.
"""

import os
import pytest
from rich.console import Console

from aztec_circle.config import settings
from aztec_circle.engine.config_manager import ConfigManager
from aztec_circle.engine.state_machine import AztecOrchestrator
from aztec_circle.domain.models import CircleRunState
from aztec_circle.tui.session import SessionState
from aztec_circle.tui.commands import dispatch_slash_command
from aztec_circle.tui.config_ui import render_ranks_table


def test_granular_model_resolution_hierarchy():
    # 1. Baseline: sub-roles inherit from parent rank
    settings.YOUTH_MODEL = "gemini/gemini-3.7-flash"
    settings.YOUTH_CHAOS_MODEL = None
    settings.YOUTH_ADVOCATE_MODEL = None
    settings.PEER_MODEL = "anthropic/claude-sonnet-5"
    settings.PATCH_MODEL = None
    settings.FIXER_MODEL = None
    settings.ELDER_MODEL = "gemini/gemini-2.5-pro"
    settings.ELDER_SECURITY_MODEL = None
    settings.ELDER_STRUCTURAL_MODEL = None

    assert settings.get_effective_model("YOUTH_CHAOS") == "gemini/gemini-3.7-flash"
    assert settings.get_effective_model("YOUTH_ADVOCATE") == "gemini/gemini-3.7-flash"
    assert settings.get_effective_model("PATCH") == "anthropic/claude-sonnet-5"
    assert settings.get_effective_model("FIXER") == "anthropic/claude-sonnet-5"
    assert settings.get_effective_model("ELDER_SECURITY") == "gemini/gemini-2.5-pro"
    assert settings.get_effective_model("ELDER_STRUCTURAL") == "gemini/gemini-2.5-pro"

    # 2. Granular override for specific sub-role
    settings.ELDER_SECURITY_MODEL = "deepseek/deepseek-r1"
    assert settings.get_effective_model("ELDER_SECURITY") == "deepseek/deepseek-r1"
    # Structural still inherits from ELDER_MODEL
    assert settings.get_effective_model("ELDER_STRUCTURAL") == "gemini/gemini-2.5-pro"

    # 3. Patch model override
    settings.PATCH_MODEL = "anthropic/claude-haiku-4-5"
    assert settings.get_effective_model("PATCH") == "anthropic/claude-haiku-4-5"
    assert settings.get_effective_model("PEER") == "anthropic/claude-sonnet-5"

    # Cleanup
    settings.ELDER_SECURITY_MODEL = None
    settings.PATCH_MODEL = None


def test_config_manager_save_and_reset_model_assignment():
    # Test setting granular role
    ConfigManager.save_model_assignment("ELDER_SECURITY", "deepseek/deepseek-r1")
    assert settings.ELDER_SECURITY_MODEL == "deepseek/deepseek-r1"
    assert settings.get_effective_model("ELDER_SECURITY") == "deepseek/deepseek-r1"

    # Test status list
    status = ConfigManager.get_granular_roles_status()
    sec_item = next(item for item in status if item["role_key"] == "ELDER_SECURITY")
    assert sec_item["is_override"] is True
    assert sec_item["effective_model"] == "deepseek/deepseek-r1"

    # Test reset
    ConfigManager.reset_model_assignment("ELDER_SECURITY")
    assert settings.ELDER_SECURITY_MODEL is None
    assert settings.get_effective_model("ELDER_SECURITY") == settings.ELDER_MODEL


def test_orchestrator_initializes_with_granular_models():
    settings.YOUTH_CHAOS_MODEL = "anthropic/claude-haiku-4-5"
    settings.ELDER_SECURITY_MODEL = "deepseek/deepseek-r1"
    settings.ELDER_STRUCTURAL_MODEL = "anthropic/claude-opus-5"

    state = CircleRunState(goal="Test Granular Model Orchestration")
    orchestrator = AztecOrchestrator(state=state)

    chaos_agent = next(a for a in orchestrator.youth_agents if a.persona == "chaos_brainstormer")
    assert chaos_agent.model == "anthropic/claude-haiku-4-5"

    sec_elder = next(a for a in orchestrator.elder_agents if a.persona == "security_governance")
    assert sec_elder.model == "deepseek/deepseek-r1"

    struct_elder = next(a for a in orchestrator.elder_agents if a.persona == "structural_perf")
    assert struct_elder.model == "anthropic/claude-opus-5"

    # Cleanup
    settings.YOUTH_CHAOS_MODEL = None
    settings.ELDER_SECURITY_MODEL = None
    settings.ELDER_STRUCTURAL_MODEL = None


@pytest.mark.asyncio
async def test_tui_slash_models_granular_commands():
    state = SessionState()
    console = Console(record=True)

    # 1. View /models table
    handled = await dispatch_slash_command("/models", state, console)
    assert handled is True
    output = console.export_text()
    assert "Active Aztec Rank" in output
    assert "Youth" in output
    assert "Elder" in output

    # 2. Set granular model via /models set
    console = Console(record=True)
    handled = await dispatch_slash_command("/models set elder_security deepseek/deepseek-r1", state, console)
    assert handled is True
    assert settings.ELDER_SECURITY_MODEL == "deepseek/deepseek-r1"

    # 3. Reset granular model via /models reset
    console = Console(record=True)
    handled = await dispatch_slash_command("/models reset elder_security", state, console)
    assert handled is True
    assert settings.ELDER_SECURITY_MODEL is None
