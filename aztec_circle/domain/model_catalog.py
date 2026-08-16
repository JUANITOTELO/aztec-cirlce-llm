"""
Curated model catalog and presets powered by LiteLLM introspection.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import litellm


@dataclass
class ModelInfo:
    """Represents metadata and capabilities for an LLM model."""
    id: str
    name: str
    provider: str
    required_key: Optional[str]
    context_k: int
    multimodal: bool
    reasoning: bool
    supports_tools: bool
    description: str
    recommended_ranks: List[str]

    @property
    def is_configured(self) -> bool:
        """Check if environment has required credentials for this model."""
        if not self.required_key:
            return True
        val = os.environ.get(self.required_key)
        return bool(val and len(val.strip()) > 5)


# Provider Key Mapping
PROVIDER_KEY_MAP = {
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "cohere": "COHERE_API_KEY",
    "ollama": None,
}

# Curated List of Top Production Frontier Models
CURATED_MODELS: List[Dict[str, Any]] = [
    # Anthropic Claude (Generation 5 & 4.5 - Official 2026 Schedule)
    {
        "id": "anthropic/claude-fable-5",
        "name": "Claude Fable 5",
        "provider": "anthropic",
        "description": "Next-generation intelligence for long-running agents (adaptive thinking)",
        "recommended_ranks": ["PEER", "ELDER"],
        "input_cost_per_m": 10.00,
        "output_cost_per_m": 50.00,
        "cache_hit_cost_per_m": 1.00,
    },
    {
        "id": "anthropic/claude-opus-5",
        "name": "Claude Opus 5",
        "provider": "anthropic",
        "description": "Complex agentic coding and enterprise architecture (adaptive thinking)",
        "recommended_ranks": ["ELDER", "PEER"],
        "input_cost_per_m": 5.00,
        "output_cost_per_m": 25.00,
        "cache_hit_cost_per_m": 0.50,
    },
    {
        "id": "anthropic/claude-sonnet-5",
        "name": "Claude Sonnet 5",
        "provider": "anthropic",
        "description": "Best combination of speed, reasoning, and coding intelligence ($2 in / $10 out)",
        "recommended_ranks": ["PEER", "ELDER"],
        "input_cost_per_m": 2.00,
        "output_cost_per_m": 10.00,
        "cache_hit_cost_per_m": 0.20,
    },
    {
        "id": "anthropic/claude-haiku-4-5",
        "name": "Claude Haiku 4.5",
        "provider": "anthropic",
        "description": "Fastest near-frontier model with extended thinking ($1 in / $5 out)",
        "recommended_ranks": ["YOUTH", "FALLBACK"],
        "input_cost_per_m": 1.00,
        "output_cost_per_m": 5.00,
        "cache_hit_cost_per_m": 0.10,
    },
    # OpenAI (GPT-5.6 Series)
    {
        "id": "openai/gpt-5.6-sol",
        "name": "GPT-5.6 Sol",
        "provider": "openai",
        "description": "Flagship multi-step reasoning, professional coding & cyber security",
        "recommended_ranks": ["ELDER", "PEER"],
        "input_cost_per_m": 5.00,
        "output_cost_per_m": 20.00,
        "cache_hit_cost_per_m": 0.50,
    },
    {
        "id": "openai/gpt-5.6-terra",
        "name": "GPT-5.6 Terra",
        "provider": "openai",
        "description": "Balanced workhorse for everyday development & agentic synthesis",
        "recommended_ranks": ["PEER", "YOUTH"],
        "input_cost_per_m": 2.50,
        "output_cost_per_m": 10.00,
        "cache_hit_cost_per_m": 0.25,
    },
    {
        "id": "openai/gpt-5.6-luna",
        "name": "GPT-5.6 Luna",
        "provider": "openai",
        "description": "Ultra-fast, cost-effective high-volume brainstormer",
        "recommended_ranks": ["YOUTH", "FALLBACK"],
        "input_cost_per_m": 0.75,
        "output_cost_per_m": 3.00,
        "cache_hit_cost_per_m": 0.075,
    },
    # Google Gemini (Gemini 3 & 2.5 Generation)
    {
        "id": "gemini/gemini-3.7-flash",
        "name": "Gemini 3.7 Flash",
        "provider": "gemini",
        "description": "Next-gen hybrid reasoning & multimodal speed flagship for agentic coding",
        "recommended_ranks": ["YOUTH", "PEER", "ELDER", "FALLBACK"],
        "input_cost_per_m": 0.075,
        "output_cost_per_m": 0.30,
        "cache_hit_cost_per_m": 0.01875,
    },
    {
        "id": "gemini/gemini-3.1-pro",
        "name": "Gemini 3.1 Pro",
        "provider": "gemini",
        "description": "Flagship reasoning & complex multi-file architectural planning",
        "recommended_ranks": ["ELDER", "PEER"],
        "input_cost_per_m": 1.25,
        "output_cost_per_m": 5.00,
        "cache_hit_cost_per_m": 0.3125,
    },
    {
        "id": "gemini/gemini-2.5-pro",
        "name": "Gemini 2.5 Pro",
        "provider": "gemini",
        "description": "Deep multi-file architecture & reasoning titan (2M context)",
        "recommended_ranks": ["PEER", "ELDER"],
        "input_cost_per_m": 1.25,
        "output_cost_per_m": 5.00,
        "cache_hit_cost_per_m": 0.3125,
    },
    {
        "id": "gemini/gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "gemini",
        "description": "Ultra low-latency, high throughput multimodal model",
        "recommended_ranks": ["YOUTH", "FALLBACK"],
        "input_cost_per_m": 0.075,
        "output_cost_per_m": 0.30,
        "cache_hit_cost_per_m": 0.01875,
    },
    {
        "id": "gemini/gemini-3.1-flash-lite",
        "name": "Gemini 3.1 Flash-Lite",
        "provider": "gemini",
        "description": "Ultra low-cost, high-speed multimodal model ($0.025 in / $0.10 out)",
        "recommended_ranks": ["YOUTH", "PEER", "FALLBACK"],
        "input_cost_per_m": 0.025,
        "output_cost_per_m": 0.10,
        "cache_hit_cost_per_m": 0.00625,
    },
    {
        "id": "gemini/gemini-2.5-flash-lite",
        "name": "Gemini 2.5 Flash-Lite",
        "provider": "gemini",
        "description": "High-volume, cost-effective subagent & repair automation",
        "recommended_ranks": ["YOUTH", "FALLBACK"],
        "input_cost_per_m": 0.0375,
        "output_cost_per_m": 0.15,
        "cache_hit_cost_per_m": 0.01,
    },
    # DeepSeek
    {
        "id": "deepseek/deepseek-r1",
        "name": "DeepSeek R1",
        "provider": "deepseek",
        "description": "Open-weights reasoning model for algorithmic & structural review",
        "recommended_ranks": ["ELDER", "PEER"],
        "input_cost_per_m": 0.55,
        "output_cost_per_m": 2.19,
        "cache_hit_cost_per_m": 0.14,
    },
    {
        "id": "deepseek/deepseek-chat",
        "name": "DeepSeek V3",
        "provider": "deepseek",
        "description": "Cost-effective general coding and synthetic instruction",
        "recommended_ranks": ["PEER", "YOUTH"],
        "input_cost_per_m": 0.27,
        "output_cost_per_m": 1.10,
        "cache_hit_cost_per_m": 0.07,
    },
    # Groq (Ultra-Fast Inference)
    {
        "id": "groq/llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B (Groq)",
        "provider": "groq",
        "description": "Ultra-fast open-weights flagship on Groq LPU hardware",
        "recommended_ranks": ["YOUTH", "FALLBACK"],
        "input_cost_per_m": 0.59,
        "output_cost_per_m": 0.79,
        "cache_hit_cost_per_m": 0.10,
    },
    {
        "id": "groq/llama-3.1-8b-instant",
        "name": "Llama 3.1 8B (Groq)",
        "provider": "groq",
        "description": "Instantaneous 8B inference for rapid ideation and filtering",
        "recommended_ranks": ["YOUTH", "FALLBACK"],
        "input_cost_per_m": 0.05,
        "output_cost_per_m": 0.08,
        "cache_hit_cost_per_m": 0.01,
    },
    # Local Ollama Models (Zero Cost)
    {
        "id": "ollama/llama3.2",
        "name": "Llama 3.2 3B (Local)",
        "provider": "ollama",
        "description": "Local offline model running via Ollama",
        "recommended_ranks": ["YOUTH", "FALLBACK"],
        "input_cost_per_m": 0.00,
        "output_cost_per_m": 0.00,
        "cache_hit_cost_per_m": 0.00,
    },
    {
        "id": "ollama/qwen2.5-coder:7b",
        "name": "Qwen 2.5 Coder 7B (Local)",
        "provider": "ollama",
        "description": "Local coding specialist running via Ollama",
        "recommended_ranks": ["PEER"],
        "input_cost_per_m": 0.00,
        "output_cost_per_m": 0.00,
        "cache_hit_cost_per_m": 0.00,
    },
    {
        "id": "ollama/deepseek-r1:8b",
        "name": "DeepSeek R1 8B (Local)",
        "provider": "ollama",
        "description": "Local offline reasoning auditor",
        "recommended_ranks": ["ELDER"],
        "input_cost_per_m": 0.00,
        "output_cost_per_m": 0.00,
        "cache_hit_cost_per_m": 0.00,
    },
]


PRESET_CONFIGURATIONS = {
    "speed_budget": {
        "name": "⚡ Speed & Budget",
        "description": "All Gemini 3.7 Flash + Groq Failover for maximum speed and lowest spend",
        "models": {
            "YOUTH": "gemini/gemini-3.7-flash",
            "PEER": "gemini/gemini-3.7-flash",
            "ELDER": "gemini/gemini-3.7-flash",
            "FALLBACK": "groq/llama-3.3-70b-versatile",
        },
    },
    "anthropic_efficiency": {
        "name": "🏰 Anthropic Smart Budget (Sonnet 5 + Haiku 4.5)",
        "description": "Optimal price-performance Anthropic suite: Haiku 4.5 for Youth & Fallback ($1/MTok), Sonnet 5 for Peer & Elder ($2/MTok)",
        "models": {
            "YOUTH": "anthropic/claude-haiku-4-5",
            "PEER": "anthropic/claude-sonnet-5",
            "ELDER": "anthropic/claude-sonnet-5",
            "FALLBACK": "anthropic/claude-haiku-4-5",
        },
    },
    "anthropic_suite": {
        "name": "🏰 Anthropic Claude 5 Suite",
        "description": "Haiku 4.5 for Youth & Fallback ($1/MTok), Sonnet 5 for Peer & Elder ($2/MTok)",
        "models": {
            "YOUTH": "anthropic/claude-haiku-4-5",
            "PEER": "anthropic/claude-sonnet-5",
            "ELDER": "anthropic/claude-sonnet-5",
            "FALLBACK": "anthropic/claude-haiku-4-5",
        },
    },
    "anthropic_budget": {
        "name": "⚡ Anthropic Ultra-Low Cost (All Haiku 4.5)",
        "description": "Entire pipeline powered by Claude Haiku 4.5 ($1.00/MTok base, $0.10 cached) for lightning speed and lowest spend",
        "models": {
            "YOUTH": "anthropic/claude-haiku-4-5",
            "PEER": "anthropic/claude-haiku-4-5",
            "ELDER": "anthropic/claude-haiku-4-5",
            "FALLBACK": "anthropic/claude-haiku-4-5",
        },
    },
    "anthropic_opus_flagship": {
        "name": "👑 Anthropic Flagship Reasoning (Opus 5 + Sonnet 5)",
        "description": "Haiku 4.5 (Youth) -> Sonnet 5 (Peer) -> Opus 5 (Elder) for deep architectural auditing",
        "models": {
            "YOUTH": "anthropic/claude-haiku-4-5",
            "PEER": "anthropic/claude-sonnet-5",
            "ELDER": "anthropic/claude-opus-5",
            "FALLBACK": "anthropic/claude-haiku-4-5",
        },
    },
    "max_reasoning": {
        "name": "🧠 Maximum Reasoning & Code Quality",
        "description": "Gemini 3.7 Flash (Youth) -> Claude Sonnet 5 (Peer) -> Claude Opus 5 (Elder)",
        "models": {
            "YOUTH": "gemini/gemini-3.7-flash",
            "PEER": "anthropic/claude-sonnet-5",
            "ELDER": "anthropic/claude-opus-5",
            "FALLBACK": "gemini/gemini-2.5-pro",
        },
    },
    "google_suite": {
        "name": "💎 Google Gemini Ultra Suite",
        "description": "Gemini 3.7 Flash for Youth, Gemini 2.5 Pro for Peer & Elder Council",
        "models": {
            "YOUTH": "gemini/gemini-3.7-flash",
            "PEER": "gemini/gemini-2.5-pro",
            "ELDER": "gemini/gemini-2.5-pro",
            "FALLBACK": "gemini/gemini-2.5-flash",
        },
    },
    "openai_suite": {
        "name": "🤖 OpenAI GPT-5.6 Suite",
        "description": "GPT-5.6 Luna (Youth) -> GPT-5.6 Terra (Peer) -> GPT-5.6 Sol (Elder)",
        "models": {
            "YOUTH": "openai/gpt-5.6-luna",
            "PEER": "openai/gpt-5.6-terra",
            "ELDER": "openai/gpt-5.6-sol",
            "FALLBACK": "gemini/gemini-3.7-flash",
        },
    },
    "local_offline": {
        "name": "🏠 Local / Offline (Ollama)",
        "description": "Run Aztec completely offline on local hardware with zero API costs",
        "models": {
            "YOUTH": "ollama/llama3.2",
            "PEER": "ollama/qwen2.5-coder:7b",
            "ELDER": "ollama/deepseek-r1:8b",
            "FALLBACK": "ollama/llama3.2",
        },
    },
}


class ModelCatalog:
    """Introspects and queries model capabilities using LiteLLM."""

    @classmethod
    def get_model_info(cls, model_id: str) -> ModelInfo:
        """Fetch model metadata enriched with LiteLLM introspection."""
        # Find curated entry or create a generic one
        curated = next((m for m in CURATED_MODELS if m["id"] == model_id), None)
        provider = model_id.split("/")[0] if "/" in model_id else "unknown"
        req_key = PROVIDER_KEY_MAP.get(provider, None)

        context_k = 128
        multimodal = False
        reasoning = False
        supports_tools = True

        try:
            info = litellm.get_model_info(model_id)
            if info:
                max_inp = info.get("max_input_tokens") or info.get("max_tokens") or 128000
                context_k = int(max_inp // 1000) if max_inp else 128
                multimodal = bool(info.get("supports_vision") or info.get("supports_pdf_input"))
                reasoning = bool(info.get("supports_reasoning") or "r1" in model_id or "o1" in model_id or "o3" in model_id or "3.7" in model_id)
                supports_tools = bool(info.get("supports_function_calling", True))
        except Exception:
            if "gemini" in model_id or "gpt-4o" in model_id or "claude" in model_id:
                multimodal = True
            if "r1" in model_id or "o1" in model_id or "o3" in model_id or "3.7" in model_id or "2.5-pro" in model_id:
                reasoning = True

        return ModelInfo(
            id=model_id,
            name=curated["name"] if curated else model_id,
            provider=curated["provider"] if curated else provider,
            required_key=req_key,
            context_k=context_k,
            multimodal=multimodal,
            reasoning=reasoning,
            supports_tools=supports_tools,
            description=curated["description"] if curated else f"{provider.capitalize()} LLM via LiteLLM",
            recommended_ranks=curated["recommended_ranks"] if curated else ["PEER", "FALLBACK"],
        )

    @classmethod
    def list_curated_models(cls, provider: Optional[str] = None, rank: Optional[str] = None) -> List[ModelInfo]:
        """List curated models filtered optionally by provider or rank."""
        models: List[ModelInfo] = []
        for m in CURATED_MODELS:
            if provider and m["provider"] != provider.lower():
                continue
            if rank and rank.upper() not in m["recommended_ranks"]:
                continue
            models.append(cls.get_model_info(m["id"]))
        return models

    @classmethod
    def list_providers(cls) -> List[str]:
        """List distinct providers in curated catalog."""
        return ["gemini", "anthropic", "openai", "deepseek", "groq", "mistral", "ollama"]

    @classmethod
    def get_model_pricing(cls, model_id: str) -> Tuple[float, float]:
        """
        Return (input_cost_per_m, output_cost_per_m) for model_id.
        Defaults to (3.00, 15.00) if not explicitly registered.
        """
        curated = next((m for m in CURATED_MODELS if m["id"] == model_id), None)
        if curated and "input_cost_per_m" in curated and "output_cost_per_m" in curated:
            return (float(curated["input_cost_per_m"]), float(curated["output_cost_per_m"]))
        return (3.00, 15.00)
