"""
Base agent abstractions and structured JSON response parsing.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
import structlog
from pydantic import BaseModel

from aztec_circle.adapters.llm_provider import LLMProvider, LLMResponse
from aztec_circle.domain.models import AgentRank

log = structlog.get_logger(__name__)


def extract_json_payload(text: str) -> Dict[str, Any]:
    """
    Robustly extract JSON from model responses, handling markdown code fences,
    leading/trailing chatter, unescaped newlines, trailing commas, or partial JSON.
    """
    text = text.strip()
    if not text:
        return {}

    candidates: List[str] = []

    # 1. Strip markdown code fences if present
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)(?:```|$)"
    match = re.search(fence_pattern, text)
    if match:
        candidates.append(match.group(1).strip())

    # 2. Outermost braces
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidates.append(text[first_brace : last_brace + 1].strip())

    candidates.append(text)

    for cand in candidates:
        if not cand:
            continue
        # Direct parse with strict=False
        try:
            return json.loads(cand, strict=False)
        except json.JSONDecodeError:
            pass

        # Cleanup trailing commas: ,} or ,]
        cleaned = re.sub(r",\s*([\]}])", r"\1", cand)
        try:
            return json.loads(cleaned, strict=False)
        except json.JSONDecodeError:
            pass

    log.warning("agent.json_extraction_failed", preview=text[:160])
    return {}


class BaseAgent:
    def __init__(
        self,
        agent_id: str,
        rank: AgentRank,
        model: Optional[str] = None,
        provider: Optional[LLMProvider] = None,
    ):
        self.agent_id = agent_id
        self.rank = rank
        self.model = model
        self.provider = provider or LLMProvider(primary_model=model)

    async def _invoke_llm(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        thinking_budget: Optional[int] = None,
    ) -> LLMResponse:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return await self.provider.complete(
            messages=messages,
            model=self.model,
            temperature=temperature,
            thinking_budget=thinking_budget,
        )
