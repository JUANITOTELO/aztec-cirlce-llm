"""
Elder Rank Agent: Security & Governance Auditor and Structural & Performance Auditor.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import structlog

from aztec_circle.agents.base import BaseAgent, extract_json_payload
from aztec_circle.config import settings
from aztec_circle.domain.models import (
    AgentRank,
    ElderAuditItem,
    ElderVerdict,
    PeerDraftOutput,
    VerdictStatus,
)
from aztec_circle.prompts import render

log = structlog.get_logger(__name__)


class ElderAgent(BaseAgent):
    def __init__(
        self,
        persona: str = "security_governance",
        model: Optional[str] = None,
        provider: Optional[Any] = None,
        thinking_budget: Optional[int] = None,
    ):
        model_name = model or settings.ELDER_MODEL
        super().__init__(
            agent_id=f"elder_{persona}",
            rank=AgentRank.ELDER,
            model=model_name,
            provider=provider,
        )
        self.persona = persona
        self.thinking_budget = (
            thinking_budget if thinking_budget is not None else settings.ELDER_THINKING_BUDGET
        )

    async def audit(self, draft: PeerDraftOutput, original_goal: str) -> ElderVerdict:
        """
        Perform rigorous, zero-temperature audit of the peer draft.
        """
        template_name = "elder_security" if self.persona == "security_governance" else "elder_structural"
        system_prompt = render(template_name)

        code_repr = json.dumps(draft.implementation_code, indent=2)
        user_message = (
            f"ORIGINAL GOAL:\n{original_goal}\n\n"
            f"PEER ARCHITECTURE OVERVIEW:\n{draft.architecture_overview}\n\n"
            f"PEER IMPLEMENTATION CODE:\n{code_repr}\n\n"
            f"PEER MITIGATIONS APPLIED:\n{draft.mitigations_applied}\n\n"
            "Audit this implementation thoroughly and return your verdict strictly adhering to the JSON schema."
        )

        resp = await self._invoke_llm(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.0,
            thinking_budget=self.thinking_budget,
        )

        data = extract_json_payload(resp.content)
        return self._build_verdict(data, resp)

    def _build_verdict(self, data: Dict[str, Any], resp: Any) -> ElderVerdict:
        raw_items = data.get("audit_items", [])
        audit_items: List[ElderAuditItem] = []

        total_weighted_sum = 0.0
        total_weight = 0.0

        for it in raw_items:
            if isinstance(it, dict):
                w = float(it.get("weight", 0.2))
                s = float(it.get("score", 7.0))
                p = bool(it.get("passed", s >= 7.0))
                audit_items.append(
                    ElderAuditItem(
                        criterion=it.get("criterion", "Quality & Compliance"),
                        weight=w,
                        score=s,
                        critique=it.get("critique", "No critique provided"),
                        passed=p,
                    )
                )
                total_weighted_sum += w * s
                total_weight += w

        calculated_score = (
            round(total_weighted_sum / total_weight, 2)
            if total_weight > 0
            else float(data.get("weighted_score", 7.0))
        )

        flaws = data.get("critical_flaws", [])
        if not isinstance(flaws, list):
            flaws = [str(flaws)] if flaws else []

        status_str = str(data.get("status", "REJECTED")).upper()
        if flaws or calculated_score < 8.0:
            status = VerdictStatus.REJECTED
        elif status_str == "APPROVED":
            status = VerdictStatus.APPROVED
        else:
            status = VerdictStatus.REJECTED

        instructions = data.get("reworking_instructions")
        if status == VerdictStatus.REJECTED and not instructions and flaws:
            instructions = "Fix the following critical flaws:\n" + "\n".join(f"- {f}" for f in flaws)

        return ElderVerdict(
            agent_id=self.agent_id,
            persona=self.persona,
            status=status,
            weighted_score=calculated_score,
            audit_items=audit_items,
            critical_flaws=flaws,
            reworking_instructions=instructions,
            thinking_summary=data.get("thinking_summary"),
            input_tokens=resp.prompt_tokens,
            output_tokens=resp.completion_tokens,
            tokens_used=resp.total_tokens,
        )
