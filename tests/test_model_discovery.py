"""
Tests for dynamic model discovery: OpenRouter live catalog, local Ollama /
LM Studio sources, TTL cache, unified merge, pricing bridge, and the
lmstudio/ virtual routing namespace in LLMProvider.
"""

from __future__ import annotations

import json
import time

import pytest

from aztec_circle.adapters import model_discovery as md
from aztec_circle.config import settings
from aztec_circle.domain.model_catalog import ModelCatalog


# ── Normalizers ──────────────────────────────────────────────────────────────

def test_openrouter_entry_normalization():
    entry = {
        "id": "qwen/qwen3-coder",
        "name": "Qwen3 Coder",
        "context_length": 262144,
        "pricing": {"prompt": "0.0000002", "completion": "0.000001"},  # USD/token
        "architecture": {"input_modalities": ["text", "image"]},
        "supported_parameters": ["tools", "reasoning"],
    }
    dm = md._normalize_openrouter_entry(entry)
    assert dm.id == "openrouter/qwen/qwen3-coder"
    assert dm.context_k == 262
    assert dm.input_cost_per_m == pytest.approx(0.2)
    assert dm.output_cost_per_m == pytest.approx(1.0)
    assert dm.multimodal is True
    assert dm.reasoning is True


def test_openrouter_free_model_ranks_as_youth():
    entry = {
        "id": "meta-llama/free-8b",
        "pricing": {"prompt": "0", "completion": "0"},
        "architecture": {"input_modalities": ["text"]},
    }
    dm = md._normalize_openrouter_entry(entry)
    assert dm.output_cost_per_m == 0.0
    assert "YOUTH" in dm.recommended_ranks


def test_ollama_entry_normalization():
    dm = md._normalize_ollama_entry("qwen2.5-coder:7b", "http://localhost:11434")
    assert dm.id == "ollama/qwen2.5-coder:7b"
    assert dm.provider == "ollama"
    assert dm.input_cost_per_m == 0.0
    assert "PEER" in dm.recommended_ranks  # coder keyword


# ── Cache + fetch flow (mocked HTTP) ─────────────────────────────────────────

class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    @property
    def status_code(self):
        return 200

    def json(self):
        return self._payload


@pytest.mark.asyncio
async def test_fetch_openrouter_uses_cache_until_ttl_expires(monkeypatch, tmp_path):
    monkeypatch.setattr(md, "cache_path", lambda: tmp_path / "cache.json")

    calls = {"n": 0}

    async def fake_get(url, headers=None):
        calls["n"] += 1
        return {"data": [{"id": "vendor/model-a", "name": "Model A"}]}

    monkeypatch.setattr(md, "_http_get_json", fake_get)

    first = await md.fetch_openrouter(force=True)
    assert len(first) == 1 and calls["n"] == 1

    # Within TTL: cache hit, no new HTTP call.
    second = await md.fetch_openrouter(force=False)
    assert calls["n"] == 1
    assert second[0].id == "openrouter/vendor/model-a"

    # Expire the cache entry -> refetches.
    cache = md.load_cache()
    cache["sources"]["openrouter"]["fetched_at"] = time.time() - 999999
    md.save_cache(cache)
    await md.fetch_openrouter(force=False)
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_refresh_all_reports_unavailable_sources(monkeypatch, tmp_path):
    monkeypatch.setattr(md, "cache_path", lambda: tmp_path / "cache.json")

    async def fail_get(url, headers=None):
        raise ConnectionError("no network")

    async def ok_tags(url, headers=None):
        return {"models": [{"name": "llama3.2"}]}

    async def fail_get2(url, headers=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(md, "_http_get_json", lambda url, headers=None: (
        fail_tags(url) if "/api/tags" in url else fail_get(url)
    ))

    async def fail_tags(url):
        raise ConnectionError("offline ollama")

    # Route per-source: openrouter fails, ollama succeeds via tags, lmstudio disabled.
    async def smart_get(url, headers=None):
        if url.startswith("https://openrouter.ai"):
            raise ConnectionError("no network")
        if "/api/tags" in url:
            return await ok_tags(url, headers)
        raise RuntimeError("boom")

    monkeypatch.setattr(md, "_http_get_json", smart_get)

    statuses = await md.refresh_all(force=True)
    assert "unavailable" in statuses["openrouter"]
    assert statuses["ollama"] == "1 models"
    assert statuses["lmstudio"] == "unavailable" or statuses["lmstudio"].startswith(("0", "unavailable")) or statuses["lmstudio"] == "0 models"


# ── Unified catalog + pricing bridge ─────────────────────────────────────────

def test_unified_catalog_merges_dynamic_over_curated(monkeypatch, tmp_path):
    monkeypatch.setattr(md, "cache_path", lambda: tmp_path / "cache.json")

    now = time.time()
    dynamic = [
        md.DiscoveredModel(
            id="gemini/gemini-2.5-pro", name="Gemini 2.5 Pro [live]", provider="gemini",
            context_k=2000, input_cost_per_m=1.25, output_cost_per_m=5.0,
            fetched_at=now,
        ),
        md.DiscoveredModel(
            id="ollama/qwen3:32b", name="qwen3:32b (local)", provider="ollama",
            fetched_at=now,
        ),
    ]
    md.store_models("openrouter", [dynamic[0]])
    md.store_models("ollama", [dynamic[1]])

    merged = md.unified_catalog()
    by_id = {m.id: m for m in merged}
    # Dynamic wins over curated on collision.
    assert "Gemini 2.5 Pro [live]" in by_id["gemini/gemini-2.5-pro"].name
    assert "ollama/qwen3:32b" in by_id

    # Provider filter.
    local_only = md.unified_catalog(provider="ollama")
    assert all(m.provider == "ollama" for m in local_only)

    # Search filter.
    hits = md.unified_catalog(search="qwen3")
    assert any("qwen3" in m.id.lower() for m in hits)


def test_model_catalog_pricing_prefers_dynamic(monkeypatch, tmp_path):
    monkeypatch.setattr(md, "cache_path", lambda: tmp_path / "cache.json")

    md.store_models("openrouter", [
        md.DiscoveredModel(
            id="openrouter/vendor/exotic-model", name="Exotic", provider="openrouter",
            input_cost_per_m=0.13, output_cost_per_m=0.66, fetched_at=time.time(),
        ),
        md.DiscoveredModel(
            id="ollama/tinyllama", name="tinyllama (local)", provider="ollama",
            fetched_at=time.time(),
        ),
    ])

    # Unknown-to-curated model resolves real pricing from discovery cache.
    assert ModelCatalog.get_model_pricing("openrouter/vendor/exotic-model") == (pytest.approx(0.13), pytest.approx(0.66))
    # Local models are genuinely free.
    assert ModelCatalog.get_model_pricing("ollama/tinyllama") == (0.0, 0.0)
    # Curated still resolves without any cache entry for it.
    assert ModelCatalog.get_model_pricing("anthropic/claude-haiku-4-5") == (1.00, 5.00)
    # Fully unknown falls back to conservative default.
    assert ModelCatalog.get_model_pricing("nope/never-heard-of-it") == (3.00, 15.00)


def test_list_discovered_models_returns_model_info(monkeypatch, tmp_path):
    monkeypatch.setattr(md, "cache_path", lambda: tmp_path / "cache.json")
    md.store_models("ollama", [
        md.DiscoveredModel(id="ollama/llava", name="llava (local)", provider="ollama",
                           multimodal=True, recommended_ranks=["YOUTH"], fetched_at=time.time()),
    ])
    infos = ModelCatalog.list_discovered_models(include_curated=False)
    llava = next(i for i in infos if i.id == "ollama/llava")
    assert llava.multimodal is True
    assert llava.required_key is None  # local model needs no API key


# ── LM Studio routing namespace ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_lmstudio_namespace_routes_to_openai_compat(monkeypatch, tmp_path):
    import litellm as _litellm
    from aztec_circle.adapters.llm_provider import LLMProvider

    monkeypatch.setattr(settings, "LMSTUDIO_BASE_URL", "http://localhost:1234/v1")

    captured = {}

    class _Msg:
        content = "hello"

    class _Choice:
        message = _Msg()

    class _Resp:
        choices = [_Choice()]
        usage = None

    async def fake_acompletion(**kwargs):
        captured.update(kwargs)
        return _Resp()

    monkeypatch.setattr(_litellm, "acompletion", fake_acompletion)

    provider = LLMProvider(primary_model="lmstudio/qwen3-32b", fallback_model=None, streaming=False)
    resp = await provider.complete(messages=[{"role": "user", "content": "hi"}], stream=False)

    assert captured["model"] == "openai/qwen3-32b"
    assert captured["api_base"] == "http://localhost:1234/v1"
    assert resp.content == "hello"
    assert resp.model.startswith("lmstudio/")  # reported under its virtual namespace


# ── TUI subcommands ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_models_local_and_search_subcommands(monkeypatch, tmp_path):
    from rich.console import Console
    from aztec_circle.tui.commands import cmd_models
    from aztec_circle.tui.session import SessionState

    monkeypatch.setattr(md, "cache_path", lambda: tmp_path / "cache.json")
    md.store_models("ollama", [
        md.DiscoveredModel(id="ollama/qwen3:8b", name="qwen3:8b (local)", provider="ollama",
                           recommended_ranks=["PEER"], fetched_at=time.time()),
    ])

    console = Console(record=True, width=220)
    state = SessionState()
    await cmd_models("local", state, console)
    text = console.export_text()
    assert "Discovered Models" in text
    assert "ollama/qwen3:8b" in text
    assert "free" in text

    console = Console(record=True, width=220)
    await cmd_models("search qwen", state, console)
    text = console.export_text()
    assert "qwen" in text

    console = Console(record=True, width=220)
    await cmd_models("search zzzz-no-match-zzzz", state, console)
    assert "No models found" in console.export_text()


@pytest.mark.asyncio
async def test_models_refresh_handles_offline_sources(monkeypatch, tmp_path):
    from rich.console import Console
    from aztec_circle.tui.commands import cmd_models
    from aztec_circle.tui.session import SessionState

    monkeypatch.setattr(md, "cache_path", lambda: tmp_path / "cache.json")

    async def offline(url, headers=None):
        raise ConnectionError("offline")

    monkeypatch.setattr(md, "_http_get_json", offline)
    monkeypatch.setattr(settings, "LMSTUDIO_BASE_URL", "")

    console = Console(record=True, width=220)
    await cmd_models("refresh", SessionState(), console)
    text = console.export_text().lower()
    assert "discover" in text or "unavailable" in text or "cached" in text


# ── llama.cpp source ─────────────────────────────────────────────────────────

def test_llamacpp_ctx_extraction_from_server_args():
    args = ["--host", "127.0.0.1", "--ctx-size", "32768", "--model", "m.gguf"]
    assert md._ctx_from_llamacpp_args(args) == 32
    assert md._ctx_from_llamacpp_args(None) == 0
    assert md._ctx_from_llamacpp_args(["--no-value-at-end"]) == 0


def test_llamacpp_entry_normalization_coder_ranks():
    entry = {
        "id": "gemma4-coding-Q6_K",
        "status": {"args": ["--alias", "x", "--ctx-size", "32768"]},
    }
    dm = md._normalize_llamacpp_entry("gemma4-coding-Q6_K", entry)
    assert dm.id == "llamacpp/gemma4-coding-Q6_K"
    assert dm.provider == "llamacpp"
    assert dm.context_k == 32
    assert dm.output_cost_per_m == 0.0
    assert dm.recommended_ranks[0] == "PEER"


@pytest.mark.asyncio
async def test_fetch_llamacpp_parses_real_payload_shape(monkeypatch, tmp_path):
    monkeypatch.setattr(md, "cache_path", lambda: tmp_path / "cache.json")

    payload = {
        "data": [{
            "id": "gemma4-coding-Q6_K",
            "object": "model",
            "owned_by": "llamacpp",
            "status": {"value": "loaded", "args": ["--ctx-size", "32768", "--flash-attn", "on"]},
        }]
    }

    async def fake_get(url, headers=None):
        assert url == "http://localhost:8080/v1/models"
        return payload

    monkeypatch.setattr(md, "_http_get_json", fake_get)

    models = await md.fetch_llamacpp(force=True)
    assert len(models) == 1
    assert models[0].id == "llamacpp/gemma4-coding-Q6_K"
    assert models[0].context_k == 32


@pytest.mark.asyncio
async def test_llamacpp_namespace_routes_to_local_server(monkeypatch):
    import litellm as _litellm
    from aztec_circle.adapters.llm_provider import LLMProvider

    monkeypatch.setattr(settings, "LLAMACPP_BASE_URL", "http://localhost:8080")

    captured = {}

    class _Msg:
        content = "local reply"

    class _Choice:
        message = _Msg()

    class _Resp:
        choices = [_Choice()]
        usage = None

    async def fake_acompletion(**kwargs):
        captured.update(kwargs)
        return _Resp()

    monkeypatch.setattr(_litellm, "acompletion", fake_acompletion)

    provider = LLMProvider(
        primary_model="llamacpp/gemma4-coding-Q6_K", fallback_model=None, streaming=False
    )
    resp = await provider.complete(messages=[{"role": "user", "content": "hi"}], stream=False)

    assert captured["model"] == "openai/gemma4-coding-Q6_K"
    assert captured["api_base"] == "http://localhost:8080/v1"
    assert resp.content == "local reply"


def test_unified_catalog_includes_llamacpp(monkeypatch, tmp_path):
    monkeypatch.setattr(md, "cache_path", lambda: tmp_path / "cache.json")
    md.store_models("llamacpp", [
        md.DiscoveredModel(id="llamacpp/gemma4-coding-Q6_K", name="gemma (local)",
                           provider="llamacpp", context_k=32, fetched_at=time.time()),
    ])
    local = [m for m in md.unified_catalog(include_curated=False) if m.provider == "llamacpp"]
    assert len(local) == 1
