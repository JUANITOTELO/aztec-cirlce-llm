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
from aztec_circle.config import settings
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
        # Agentic tool access (set by orchestrator/callers when a real
        # project exists); see _run_llm_maybe_with_tools.
        self.tool_registry: Optional[Any] = None
        self.project_root: Optional[str] = None

    async def _invoke_llm(
        self,
        system_prompt: str,
        user_message: str,
        images: Optional[List[str]] = None,
        temperature: float = 0.7,
        thinking_budget: Optional[int] = None,
        on_chunk: Optional[Any] = None,
        stream: Optional[bool] = None,
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
            on_chunk=on_chunk,
            stream=stream,
        )

    async def _run_llm_maybe_with_tools(
        self,
        system_prompt: str,
        user_message: str,
        images: Optional[List[str]] = None,
        temperature: float = 0.35,
        thinking_budget: Optional[int] = None,
        on_chunk: Optional[Any] = None,
    ) -> LLMResponse:
        """
        Single-shot LLM call when no tool registry is attached; otherwise a
        bounded ReAct-style loop: the model may issue {"tool_requests": [...]}
        instead of its final answer, results are fed back, and it gets another
        chance. Returns one LLMResponse whose token totals cover all rounds.
        """
        if self.tool_registry is None or not self.project_root:
            return await self._invoke_llm(
                system_prompt=system_prompt,
                user_message=user_message,
                images=images,
                temperature=temperature,
                thinking_budget=thinking_budget,
                on_chunk=on_chunk,
            )

        from aztec_circle.adapters.image_utils import format_multimodal_content
        from aztec_circle.tools import ToolContext
        from aztec_circle.tools.agent_bridge import (
            build_tool_prompt,
            execute_tool_requests,
            parse_tool_requests,
            render_tool_results,
        )

        tool_ctx = ToolContext(project_root=self.project_root)
        user_message = user_message + "\n\n" + build_tool_prompt(
            self.tool_registry, max_rounds=settings.AGENT_TOOLS_MAX_ROUNDS
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": format_multimodal_content(user_message, images=images)},
        ]

        total_prompt = 0
        total_completion = 0
        final_resp: Optional[LLMResponse] = None

        rounds = settings.AGENT_TOOLS_MAX_ROUNDS + 1
        for round_idx in range(rounds):
            resp = await self.provider.complete(
                messages=messages,
                model=self.model,
                temperature=temperature,
                thinking_budget=thinking_budget if thinking_budget and round_idx == 0 else None,
                on_chunk=on_chunk,
            )
            total_prompt += resp.prompt_tokens
            total_completion += resp.completion_tokens
            final_resp = resp

            if round_idx >= rounds - 1:
                break

            requests = parse_tool_requests(resp.content)
            if not requests:
                break  # genuine deliverable — no more rounds needed

            log.info("agent.tool_round", agent=self.agent_id, round=round_idx + 1,
                     requested=[r["tool"] for r in requests])
            results = await execute_tool_requests(requests, self.tool_registry, tool_ctx)
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": render_tool_results(results)})

        assert final_resp is not None
        # Fold earlier-round usage into the returned response.
        return LLMResponse(
            content=final_resp.content,
            prompt_tokens=total_prompt,
            completion_tokens=total_completion,
            total_tokens=total_prompt + total_completion,
            cached_tokens=final_resp.cached_tokens,
            model=final_resp.model,
            raw=final_resp.raw,
        )
