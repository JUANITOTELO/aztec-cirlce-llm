"""
Youth Rank Agent: Chaos Brainstormer & Devil's Advocate.
"""

from __future__ import annotations

from typing import List, Optional
import structlog

from aztec_circle.agents.base import BaseAgent, extract_json_payload
from aztec_circle.config import settings
from aztec_circle.domain.models import (
    AgentRank,
    SeverityLevel,
    YouthBrainstormOutput,
    YouthRiskItem,
)
from aztec_circle.prompts import render

log = structlog.get_logger(__name__)


class YouthAgent(BaseAgent):
    def __init__(
        self,
        persona: str = "chaos_brainstormer",
        model: Optional[str] = None,
        provider: Optional[Any] = None,
    ):
        model_name = model or settings.YOUTH_MODEL
        super().__init__(
            agent_id=f"youth_{persona}",
            rank=AgentRank.YOUTH,
            model=model_name,
            provider=provider,
        )
        self.persona = persona

    @property
    def temperature(self) -> float:
        if self.persona == "chaos_brainstormer":
            return 1.0
        return 0.9  # devils_advocate

    async def run(self, goal: str, images: Optional[List[str]] = None) -> YouthBrainstormOutput:
        """
        Execute Youth brainstorming / stress testing against the user goal and optional reference images.
        """
        prompt_name = "youth_chaos" if self.persona == "chaos_brainstormer" else "youth_advocate"
        system_prompt = render(prompt_name)
        user_message = f"GOAL / TASK TO ANALYZE:\n{goal}\n\nExecute divergent brainstorming and risk identification."

        resp = await self._invoke_llm(
            system_prompt=system_prompt,
            user_message=user_message,
            images=images,
            temperature=self.temperature,
        )

        data = extract_json_payload(resp.content)
        return self._build_output(data, resp)

    def _build_output(self, data: dict, resp: Any) -> YouthBrainstormOutput:
        raw_risks = data.get("identified_risks", [])
        risk_items: List[YouthRiskItem] = []

        for r in raw_risks:
            if isinstance(r, dict):
                sev = r.get("severity", "MEDIUM")
                if sev not in SeverityLevel.__members__:
                    sev = "MEDIUM"
                risk_items.append(
                    YouthRiskItem(
                        category=r.get("category", "general"),
                        description=r.get("description", "Identified risk"),
                        severity=SeverityLevel(sev),
                        suggested_mitigation=r.get("suggested_mitigation", "Address in design"),
                        is_showstopper=bool(r.get("is_showstopper", False)),
                    )
                )

        override_triggered = bool(data.get("override_triggered", False))
        if any(r.is_showstopper for r in risk_items):
            override_triggered = True

        return YouthBrainstormOutput(
            agent_id=self.agent_id,
            persona=self.persona,
            radical_ideas=data.get("radical_ideas", []),
            identified_risks=risk_items,
            adversarial_scenarios=data.get("adversarial_scenarios", []),
            override_triggered=override_triggered,
            override_rationale=data.get("override_rationale"),
            input_tokens=resp.prompt_tokens,
            output_tokens=resp.completion_tokens,
            tokens_used=resp.total_tokens,
        )
