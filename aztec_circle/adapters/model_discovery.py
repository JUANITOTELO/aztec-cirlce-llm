"""
Dynamic model discovery for the Aztec Decision Circle.

Replaces the brittle, hardcoded model list with live discovery:

- OpenRouter: GET https://openrouter.ai/api/v1/models (public endpoint) —
  the full 300+ model catalog with real-time pricing and capabilities.
- Ollama (local): GET {OLLAMA_BASE_URL}/api/tags — every locally installed
  model, not a fixed guess of three names.
- LM Studio / any OpenAI-compatible local server: GET {LMSTUDIO_BASE_URL}/models
  (opt-in via LMSTUDIO_BASE_URL).

Discovered models are cached to ~/.aztec/model_cache.json with a TTL so TUI
startup never blocks on the network; `refresh_all(force=True)` re-fetches.
The curated static list remains as an offline fallback and is merged
(dynamically discovered entries win on id collision).
"""

from __future__ import annotations

import json
import time
import asyncio
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import structlog

import httpx

from aztec_circle.config import settings

log = structlog.get_logger(__name__)

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
DEFAULT_LMSTUDIO_URL = "http://localhost:1234/v1"

_CACHE_VERSION = 1


@dataclass
class DiscoveredModel:
    """A model discovered from a live source (OpenRouter, Ollama, LM Studio)."""
    id: str                       # LiteLLM-routable id, e.g. "openrouter/qwen/qwen3-coder"
    name: str
    provider: str                 # "openrouter" | "ollama" | "lmstudio"
    context_k: int = 0            # 0 = unknown
    input_cost_per_m: float = 0.0
    output_cost_per_m: float = 0.0
    multimodal: bool = False
    reasoning: bool = False
    description: str = ""
    recommended_ranks: List[str] = field(default_factory=list)
    fetched_at: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DiscoveredModel":
        known = {f for f in cls.__dataclass_fields__}  # noqa: C416
        return cls(**{k: v for k, v in data.items() if k in known})


# ── Cache ────────────────────────────────────────────────────────────────────

def cache_path() -> Path:
    return Path(settings.PLASTICITY_STATE_PATH).expanduser().parent / "model_cache.json"


def _cache_ttl_seconds() -> float:
    try:
        return max(0.0, float(getattr(settings, "MODEL_DISCOVERY_TTL_HOURS", 6.0))) * 3600.0
    except (TypeError, ValueError):
        return 6 * 3600.0


def load_cache() -> Dict[str, Any]:
    try:
        path = cache_path()
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("version") == _CACHE_VERSION:
                return data
    except (json.JSONDecodeError, OSError):
        pass
    return {"version": _CACHE_VERSION, "sources": {}}


def save_cache(cache: Dict[str, Any]) -> None:
    try:
        path = cache_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache), encoding="utf-8")
        tmp.replace(path)
    except OSError as exc:
        log.warning("discovery.cache_save_failed", error=str(exc))


def get_cached_models(source: str) -> Optional[List[DiscoveredModel]]:
    """Return cached models for a source if present (regardless of age)."""
    cache = load_cache()
    entry = cache.get("sources", {}).get(source)
    if not entry:
        return None
    return [DiscoveredModel.from_dict(m) for m in entry.get("models", [])]


def cache_age_seconds(source: str) -> Optional[float]:
    """Age of a source's cache entry, or None if never fetched."""
    cache = load_cache()
    entry = cache.get("sources", {}).get(source)
    if not entry:
        return None
    return time.time() - float(entry.get("fetched_at", 0))


def store_models(source: str, models: List[DiscoveredModel]) -> None:
    cache = load_cache()
    cache.setdefault("sources", {})[source] = {
        "fetched_at": time.time(),
        "models": [m.to_dict() for m in models],
    }
    save_cache(cache)


async def _fetch_with_cache(
    source: str,
    live_fn,
    force: bool = False,
) -> List[DiscoveredModel]:
    """
    Shared fetch policy:
      fresh cache  -> serve from cache (no network)
      stale/absent -> attempt live refresh
      live failure -> serve stale cache if available, else re-raise
    """
    cached = get_cached_models(source)
    age = cache_age_seconds(source)
    if (
        not force
        and cached is not None
        and age is not None
        and age < _cache_ttl_seconds()
    ):
        return cached

    try:
        models = await live_fn()
        store_models(source, models)
        return models
    except Exception as exc:
        if cached is not None:
            log.warning(
                "discovery.refresh_failed_using_stale",
                source=source,
                error=str(exc),
                stale_age_s=int(age or 0),
            )
            return cached
        raise


# ── HTTP helper (isolated for testability) ──────────────────────────────────

async def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    try:
        timeout_s = float(getattr(settings, "MODEL_DISCOVERY_TIMEOUT_SECONDS", 8.0))
    except (TypeError, ValueError):
        timeout_s = 8.0
    timeout = httpx.Timeout(timeout_s, read=timeout_s)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers or {})
        resp.raise_for_status()
        return resp.json()


# ── Source fetchers ──────────────────────────────────────────────────────────

def _infer_ranks(input_cost: float, output_cost: float, context_k: int, model_id: str) -> List[str]:
    """Cheap heuristic so the interactive rank picker can suggest sensibly."""
    # Local / free models are great for youth brainstorming & fallback.
    if output_cost <= 0.01:
        ranks = ["YOUTH", "FALLBACK"]
        if "coder" in model_id.lower() or "code" in model_id.lower():
            ranks.insert(0, "PEER")
        return ranks
    premium = output_cost >= 10.0 or context_k >= 400
    mid = output_cost >= 2.0
    if premium:
        return ["ELDER", "PEER"]
    if mid:
        return ["PEER", "ELDER"]
    return ["YOUTH", "PEER", "FALLBACK"]


def _normalize_openrouter_entry(entry: Dict[str, Any]) -> DiscoveredModel:
    raw_id = str(entry.get("id", "")).strip()
    pricing = entry.get("pricing") or {}
    arch = entry.get("architecture") or {}

    def _per_million(val: Any) -> float:
        try:
            return round(float(val) * 1_000_000.0, 6)
        except (TypeError, ValueError):
            return 0.0

    input_cost = _per_million(pricing.get("prompt"))
    output_cost = _per_million(pricing.get("completion"))

    modalities = str(arch.get("input_modalities") or "")
    multimodal = "image" in modalities

    params = str(entry.get("supported_parameters") or "")
    lowered = raw_id.lower()
    reasoning = (
        "reasoning" in params
        or any(tok in lowered for tok in ("r1", "-o1", "o3", "o4-", "thinking", "reason"))
    )

    try:
        ctx = int(entry.get("context_length") or 0)
        context_k = ctx // 1000 if ctx else 0
    except (TypeError, ValueError):
        context_k = 0

    vendor = raw_id.split("/")[0] if "/" in raw_id else "openrouter"
    name = str(entry.get("name") or raw_id)

    return DiscoveredModel(
        id=f"openrouter/{raw_id}" if not raw_id.startswith("openrouter/") else raw_id,
        name=name,
        provider="openrouter",
        context_k=context_k,
        input_cost_per_m=input_cost,
        output_cost_per_m=output_cost,
        multimodal=multimodal,
        reasoning=reasoning,
        description=f"{vendor} via OpenRouter",
        recommended_ranks=_infer_ranks(input_cost, output_cost, context_k, raw_id),
        fetched_at=time.time(),
    )


async def fetch_openrouter(force: bool = False) -> List[DiscoveredModel]:
    """Fetch the full OpenRouter catalog (public endpoint, key optional)."""

    async def _live() -> List[DiscoveredModel]:
        headers = {}
        api_key = getattr(settings, "OPENROUTER_API_KEY", None)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = await _http_get_json(OPENROUTER_MODELS_URL, headers=headers)
        entries = payload.get("data") or []
        models = [_normalize_openrouter_entry(e) for e in entries if e.get("id")]
        log.info("discovery.openrouter_fetched", count=len(models))
        return models

    return await _fetch_with_cache("openrouter", _live, force=force)


def _normalize_ollama_entry(name: str, base_url: str) -> DiscoveredModel:
    lowered = name.lower()
    reasoning = any(t in lowered for t in ("r1", "think", "qwq", "openthinker", "deepseek-r"))
    multimodal = any(t in lowered for t in ("llava", "vision", "bakllava", "moondream", "minicpm-v", "llama3.2-vision"))
    coderish = ("coder" in lowered or "code" in lowered)
    ranks = ["YOUTH", "FALLBACK"]
    if coderish:
        ranks = ["PEER", "FALLBACK"]
    elif reasoning:
        ranks = ["ELDER", "PEER"]
    return DiscoveredModel(
        id=f"ollama/{name}",
        name=f"{name} (local)",
        provider="ollama",
        context_k=0,
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        multimodal=multimodal,
        reasoning=reasoning,
        description=f"Local Ollama model at {base_url}",
        recommended_ranks=ranks,
        fetched_at=time.time(),
    )


async def fetch_ollama(force: bool = False) -> List[DiscoveredModel]:
    base_url = (getattr(settings, "OLLAMA_BASE_URL", "") or "").rstrip("/")
    if not base_url:
        return []

    async def _live() -> List[DiscoveredModel]:
        payload = await _http_get_json(f"{base_url}/api/tags")
        names = [m.get("name") for m in (payload.get("models") or []) if m.get("name")]
        models = [_normalize_ollama_entry(n, base_url) for n in names]
        log.info("discovery.ollama_fetched", count=len(models), base_url=base_url)
        return models

    return await _fetch_with_cache("ollama", _live, force=force)


def lmstudio_base_url() -> str:
    return (getattr(settings, "LMSTUDIO_BASE_URL", "") or "").strip()


def _normalize_lmstudio_entry(model_id: str) -> DiscoveredModel:
    return DiscoveredModel(
        id=f"lmstudio/{model_id}",
        name=f"{model_id} (local)",
        provider="lmstudio",
        context_k=0,
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        multimodal=False,
        reasoning=False,
        description="Local OpenAI-compatible server (LM Studio / vLLM / llama.cpp)",
        recommended_ranks=["PEER", "FALLBACK"],
        fetched_at=time.time(),
    )


async def fetch_lmstudio(force: bool = False) -> List[DiscoveredModel]:
    base = lmstudio_base_url().rstrip("/")
    if not base:
        return []

    async def _live() -> List[DiscoveredModel]:
        url = base if base.endswith("/models") else f"{base}/models"
        headers = {}
        api_key = getattr(settings, "OPENAI_API_KEY", None)
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = await _http_get_json(url, headers=headers)
        ids = [m.get("id") for m in (payload.get("data") or []) if m.get("id")]
        models = [_normalize_lmstudio_entry(i) for i in ids]
        log.info("discovery.lmstudio_fetched", count=len(models), base_url=base)
        return models

    return await _fetch_with_cache("lmstudio", _live, force=force)


# ── llama.cpp server ─────────────────────────────────────────────────────────

def llamacpp_base_url() -> str:
    """Configured host root, e.g. http://localhost:8080."""
    return (getattr(settings, "LLAMACPP_BASE_URL", "") or "").strip().rstrip("/")


def llamacpp_api_base() -> str:
    """OpenAI-compatible API root served by llama-server."""
    root = llamacpp_base_url()
    if not root:
        return ""
    return root if root.endswith("/v1") else f"{root}/v1"


def _ctx_from_llamacpp_args(args: Any) -> int:
    """
    Extract --ctx-size from a llama-server launch arg list (or preset text).
    llama.cpp exposes its actual launch args via /v1/models status payloads.
    """
    try:
        items: List[Any] = []
        if isinstance(args, list):
            items = args
        elif isinstance(args, str):
            items = args.split()
        for i, item in enumerate(items[:-1]):
            if str(item) == "--ctx-size":
                return max(0, int(items[i + 1]) // 1000)
    except (TypeError, ValueError):
        pass
    return 0


def _normalize_llamacpp_entry(model_id: str, entry: Dict[str, Any]) -> DiscoveredModel:
    lowered = model_id.lower()
    reasoning = any(t in lowered for t in ("r1", "think", "qwq", "reason", "openthinker"))
    multimodal = any(t in lowered for t in ("llava", "vision", "minicpm-v", "bakllava", "moondream"))
    coderish = any(t in lowered for t in ("coder", "coding", "-code", "_code"))

    if coderish:
        ranks = ["PEER", "FALLBACK"]
    elif reasoning:
        ranks = ["ELDER", "PEER"]
    else:
        ranks = ["YOUTH", "PEER", "FALLBACK"]

    status = entry.get("status") or {}
    context_k = _ctx_from_llamacpp_args(status.get("args"))

    return DiscoveredModel(
        id=f"llamacpp/{model_id}",
        name=f"{model_id} (local)",
        provider="llamacpp",
        context_k=context_k,
        input_cost_per_m=0.0,
        output_cost_per_m=0.0,
        multimodal=multimodal,
        reasoning=reasoning,
        description="Local llama.cpp server (GPU/CPU GGUF inference)",
        recommended_ranks=ranks,
        fetched_at=time.time(),
    )


async def fetch_llamacpp(force: bool = False) -> List[DiscoveredModel]:
    root = llamacpp_base_url()
    if not root:
        return []

    async def _live() -> List[DiscoveredModel]:
        payload = await _http_get_json(f"{llamacpp_api_base()}/models")
        entries = [e for e in (payload.get("data") or []) if e.get("id")]
        models = [_normalize_llamacpp_entry(e["id"], e) for e in entries]
        log.info("discovery.llamacpp_fetched", count=len(models), base_url=root)
        return models

    return await _fetch_with_cache("llamacpp", _live, force=force)


SOURCES = ("openrouter", "ollama", "lmstudio", "llamacpp")


async def refresh_all(force: bool = True) -> Dict[str, str]:
    """
    Refresh every enabled source. Never raises: per-source failures are
    reported as status strings so the TUI can show exactly what happened.
    """
    statuses: Dict[str, str] = {}
    results = {
        "openrouter": fetch_openrouter(force=force),
        "ollama": fetch_ollama(force=force),
        "lmstudio": fetch_lmstudio(force=force),
        "llamacpp": fetch_llamacpp(force=force),
    }
    outcomes = await asyncio.gather(*results.values(), return_exceptions=True)
    for source, outcome in zip(results.keys(), outcomes):
        if isinstance(outcome, BaseException):
            statuses[source] = f"unavailable ({type(outcome).__name__})"
            log.debug("discovery.source_unavailable", source=source, error=str(outcome))
        else:
            statuses[source] = f"{len(outcome)} models"
    return statuses


# ── Unified sync view (cache + curated merge, never blocks on network) ──────

def unified_catalog(
    provider: Optional[str] = None,
    search: Optional[str] = None,
    include_curated: bool = True,
) -> List[DiscoveredModel]:
    """
    Merge dynamically-discovered (cached) models with the curated fallback
    list. Dynamic entries win on id collision. Purely synchronous: reads only
    the on-disk cache.
    """
    merged: Dict[str, DiscoveredModel] = {}

    if include_curated:
        from aztec_circle.domain.model_catalog import CURATED_MODELS
        now = time.time()
        for m in CURATED_MODELS:
            merged[m["id"]] = DiscoveredModel(
                id=m["id"],
                name=m["name"],
                provider=m["provider"],
                context_k=128,
                input_cost_per_m=float(m.get("input_cost_per_m", 0.0)),
                output_cost_per_m=float(m.get("output_cost_per_m", 0.0)),
                description=m.get("description", ""),
                recommended_ranks=list(m.get("recommended_ranks", [])),
                fetched_at=now,
            )

    for source in SOURCES:
        for dm in get_cached_models(source) or []:
            merged[dm.id] = dm

    models = list(merged.values())
    if provider:
        p = provider.lower().lstrip("/")
        models = [
            m for m in models
            if m.provider == p or m.id.split("/", 1)[0] == p or p in m.id.lower()
        ]
    if search:
        q = search.lower()
        models = [
            m for m in models
            if q in m.id.lower() or q in m.name.lower() or q in m.description.lower()
        ]
    models.sort(key=lambda m: (m.provider, m.id))
    return models


def lookup_dynamic_pricing(model_id: str) -> Optional[tuple]:
    """Return (input, output) per-million costs from discovery cache if known."""
    for source in SOURCES:
        for dm in get_cached_models(source) or []:
            if dm.id == model_id:
                return (dm.input_cost_per_m, dm.output_cost_per_m)
    return None
