"""
Unit tests for Anthropic prompt caching (cache_control), token discount calculations,
and permanent preset persistence across Aztec sessions.
"""

import os
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from typer.testing import CliRunner

from aztec_circle.adapters.llm_provider import LLMProvider, LLMResponse
from aztec_circle.engine.budget_manager import BudgetManager
from aztec_circle.engine.config_manager import ConfigManager
from aztec_circle.domain.model_catalog import PRESET_CONFIGURATIONS
from aztec_circle.tui.session import SessionState
from aztec_circle.config import settings
from aztec_circle.cli import app

runner = CliRunner()


def test_supports_prompt_caching_detection():
    """Verify prompt caching detection for Claude and Gemini models."""
    assert LLMProvider.supports_prompt_caching("anthropic/claude-sonnet-5") is True
    assert LLMProvider.supports_prompt_caching("anthropic/claude-opus-5") is True
    assert LLMProvider.supports_prompt_caching("anthropic/claude-haiku-4-5") is True
    assert LLMProvider.supports_prompt_caching("gemini/gemini-2.5-pro") is True
    assert LLMProvider.supports_prompt_caching("gemini/gemini-3.7-flash") is True


def test_optimize_messages_for_prompt_caching_claude():
    """Verify cache_control is injected into system prompt and long context blocks for Claude."""
    messages = [
        {"role": "system", "content": "You are Aztec Peer Architect."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "A" * 500},  # Large codebase context
                {"type": "text", "text": "Please refactor the component."},
            ],
        },
    ]

    optimized = LLMProvider.optimize_messages_for_prompt_caching(messages, "anthropic/claude-sonnet-5")

    # System message should be transformed to block with cache_control
    sys_msg = optimized[0]
    assert isinstance(sys_msg["content"], list)
    assert sys_msg["content"][0]["type"] == "text"
    assert sys_msg["content"][0]["text"] == "You are Aztec Peer Architect."
    assert sys_msg["content"][0]["cache_control"] == {"type": "ephemeral"}

    # User message's large context block should have cache_control
    user_msg = optimized[1]
    assert user_msg["content"][0]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in user_msg["content"][1]


def test_optimize_messages_skips_unsupported_models():
    """Verify messages remain untouched for non-caching models."""
    messages = [
        {"role": "system", "content": "You are a bot."},
        {"role": "user", "content": "Hello"},
    ]
    optimized = LLMProvider.optimize_messages_for_prompt_caching(messages, "ollama/llama3.2")
    assert optimized == messages


def test_budget_manager_calculates_cached_token_discount():
    """Verify that cached input tokens receive a 90% discount in BudgetManager."""
    bm = BudgetManager(input_cost_per_m=3.00, output_cost_per_m=15.00)

    # 10,000 input tokens, 8,000 of which are cached, 2,000 completion tokens
    cost = bm.record(input_tokens=10000, output_tokens=2000, cached_tokens=8000)

    # Non-cached: 2,000 tokens @ $3/M = $0.006
    # Cached: 8,000 tokens @ $0.30/M (90% discount) = $0.0024
    # Output: 2,000 tokens @ $15/M = $0.030
    # Expected total = 0.006 + 0.0024 + 0.030 = 0.0384
    assert round(cost, 5) == 0.0384
    assert bm.total_cached_tokens == 8000


def test_preset_persistence_saves_and_restores(tmp_path):
    """Verify apply_preset saves AZTEC_ACTIVE_PRESET and restores across sessions."""
    with patch.object(ConfigManager, "get_config_dir", return_value=tmp_path):
        # 1. Apply preset
        applied = ConfigManager.apply_preset("anthropic_suite")
        assert applied is True
        assert ConfigManager.get_active_preset() == "anthropic_suite"
        assert settings.PEER_MODEL == "anthropic/claude-sonnet-5"
        assert settings.ELDER_MODEL == "anthropic/claude-sonnet-5"
        assert settings.YOUTH_MODEL == "anthropic/claude-haiku-4-5"

        # 2. Simulate fresh session: reset env and load config
        os.environ.pop("AZTEC_ACTIVE_PRESET", None)
        ConfigManager.load_config_into_env()
        assert ConfigManager.get_active_preset() == "anthropic_suite"
        assert os.environ.get("AZTEC_ACTIVE_PRESET") == "anthropic_suite"

        # 3. SessionState should inherit the persistent preset
        state = SessionState()
        assert state.active_preset == "anthropic_suite"
        assert state.primary_model == "anthropic/claude-sonnet-5"


def test_cli_preset_switch_persists(tmp_path):
    """Verify CLI --preset switches and persists configuration."""
    with patch.object(ConfigManager, "get_config_dir", return_value=tmp_path):
        res = runner.invoke(app, ["config", "--preset", "openai_suite"])
        assert res.exit_code == 0
        assert ConfigManager.get_active_preset() == "openai_suite"
        assert settings.PEER_MODEL == "openai/gpt-5.6-terra"
