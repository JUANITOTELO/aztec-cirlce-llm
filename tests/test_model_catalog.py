"""
Unit tests for Aztec model catalog and presets powered by LiteLLM introspection.
"""

import pytest
from aztec_circle.domain.model_catalog import (
    ModelCatalog,
    CURATED_MODELS,
    PRESET_CONFIGURATIONS,
    PROVIDER_KEY_MAP,
)


def test_model_catalog_lists_all_curated_models():
    models = ModelCatalog.list_curated_models()
    assert len(models) == len(CURATED_MODELS)
    ids = [m.id for m in models]
    assert "gemini/gemini-3.7-flash" in ids
    assert "anthropic/claude-sonnet-5" in ids
    assert "anthropic/claude-opus-5" in ids
    assert "openai/gpt-5.6-sol" in ids
    assert "deepseek/deepseek-r1" in ids
    assert "groq/llama-3.3-70b-versatile" in ids
    assert "ollama/llama3.2" in ids


def test_model_catalog_filters_by_provider():
    gemini_models = ModelCatalog.list_curated_models(provider="gemini")
    assert len(gemini_models) >= 3
    for m in gemini_models:
        assert m.provider == "gemini"

    claude_models = ModelCatalog.list_curated_models(provider="anthropic")
    assert len(claude_models) >= 3
    for m in claude_models:
        assert m.provider == "anthropic"


def test_model_catalog_filters_by_rank():
    elder_models = ModelCatalog.list_curated_models(rank="ELDER")
    assert len(elder_models) >= 4
    for m in elder_models:
        assert "ELDER" in m.recommended_ranks


def test_model_catalog_introspects_gemini_37_flash():
    info = ModelCatalog.get_model_info("gemini/gemini-3.7-flash")
    assert info.provider == "gemini"
    assert info.required_key == "GEMINI_API_KEY"
    assert info.multimodal is True
    assert info.reasoning is True
    assert info.context_k >= 128


def test_preset_configurations_structure():
    assert "speed_budget" in PRESET_CONFIGURATIONS
    assert "max_reasoning" in PRESET_CONFIGURATIONS
    assert "google_suite" in PRESET_CONFIGURATIONS
    assert "anthropic_suite" in PRESET_CONFIGURATIONS
    assert "anthropic_efficiency" in PRESET_CONFIGURATIONS
    assert "anthropic_budget" in PRESET_CONFIGURATIONS
    assert "anthropic_opus_flagship" in PRESET_CONFIGURATIONS
    assert "openai_suite" in PRESET_CONFIGURATIONS
    assert "local_offline" in PRESET_CONFIGURATIONS

    for pid, pdata in PRESET_CONFIGURATIONS.items():
        assert "name" in pdata
        assert "models" in pdata
        assert "YOUTH" in pdata["models"]
        assert "PEER" in pdata["models"]
        assert "ELDER" in pdata["models"]
        assert "FALLBACK" in pdata["models"]


def test_model_catalog_pricing_lookup():
    in_sonnet, out_sonnet = ModelCatalog.get_model_pricing("anthropic/claude-sonnet-5")
    assert in_sonnet == 2.00
    assert out_sonnet == 10.00

    in_haiku, out_haiku = ModelCatalog.get_model_pricing("anthropic/claude-haiku-4-5")
    assert in_haiku == 1.00
    assert out_haiku == 5.00

    in_opus, out_opus = ModelCatalog.get_model_pricing("anthropic/claude-opus-5")
    assert in_opus == 5.00
    assert out_opus == 25.00
