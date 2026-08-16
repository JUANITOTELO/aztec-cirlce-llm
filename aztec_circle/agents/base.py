"""
Base agent abstractions and structured JSON response parsing.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
import json_repair
import structlog
from pydantic import BaseModel

from aztec_circle.adapters.llm_provider import LLMProvider, LLMResponse
from aztec_circle.domain.models import AgentRank

log = structlog.get_logger(__name__)


def extract_json_payload(text: str) -> Dict[str, Any]:
    """
    Robustly extract JSON from model responses using standard json with
    resilient fallback to modern json-repair engine. Handles markdown code fences,
    unescaped code newlines, trailing commas, single quotes, or truncated streams.
    """
    text = text.strip()
    if not text:
        return {}

    # 1. Direct standard parse attempt
    try:
        data = json.loads(text, strict=False)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    # 2. Modern json_repair parse directly on text
    try:
        repaired = json_repair.loads(text)
        if isinstance(repaired, dict):
            return repaired
        elif isinstance(repaired, list) and repaired and isinstance(repaired[0], dict):
            return {"items": repaired}
    except Exception:
        pass

    # 3. Strip code fences + attempt parse with json_repair
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)(?:```|$)"
    match = re.search(fence_pattern, text)
    if match:
        fence_content = match.group(1).strip()
        try:
            repaired = json_repair.loads(fence_content)
            if isinstance(repaired, dict):
                return repaired
        except Exception:
            pass

    # 4. Outermost braces slice + json_repair
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        sliced = text[first_brace : last_brace + 1].strip()
        try:
            repaired = json_repair.loads(sliced)
            if isinstance(repaired, dict):
                return repaired
        except Exception:
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
        images: Optional[List[str]] = None,
        temperature: float = 0.7,
        thinking_budget: Optional[int] = None,
    ) -> LLMResponse:
        from aztec_circle.adapters.image_utils import format_multimodal_content
        formatted_content = format_multimodal_content(user_message, images=images)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": formatted_content},
        ]
        return await self.provider.complete(
            messages=messages,
            model=self.model,
            temperature=temperature,
            thinking_budget=thinking_budget,
        )
