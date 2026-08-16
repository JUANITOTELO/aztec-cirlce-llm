"""
Peer Rank Agent: Code Drafter & System Architect.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
import structlog

from aztec_circle.adapters.mcp_client import MCPClient
from aztec_circle.agents.base import BaseAgent, extract_json_payload
from aztec_circle.config import settings
from aztec_circle.domain.models import (
    AgentRank,
    PeerDraftOutput,
    ToolCallResult,
    YouthBrainstormOutput,
)
from aztec_circle.prompts import render

log = structlog.get_logger(__name__)


class PeerAgent(BaseAgent):
    def __init__(
        self,
        agent_id: str = "peer_code_drafter",
        model: Optional[str] = None,
        provider: Optional[Any] = None,
        mcp_client: Optional[MCPClient] = None,
    ):
        model_name = model or settings.PEER_MODEL
        super().__init__(
            agent_id=agent_id,
            rank=AgentRank.PEER,
            model=model_name,
            provider=provider,
        )
        self.mcp_client = mcp_client or MCPClient()

    async def run(
        self,
        goal: str,
        youth_risks: List[YouthBrainstormOutput],
        elder_instructions: Optional[str] = None,
        loop_index: int = 0,
        images: Optional[List[str]] = None,
    ) -> PeerDraftOutput:
        """
        Execute drafting of architecture and code, addressing Youth risks, Elder critiques, and visual reference images.
        """
        is_revision = loop_index > 0 and bool(elder_instructions)
        template_name = "peer_drafter_loop" if is_revision else "peer_drafter"
        system_prompt = render(template_name, loop_index=str(loop_index))

        # Format youth risks
        formatted_risks = []
        for yo in youth_risks:
            for r in yo.identified_risks:
                formatted_risks.append(f"- [{r.severity.value}] ({r.category}) {r.description} -> Mitigation: {r.suggested_mitigation}")

        risk_context = "\n".join(formatted_risks) if formatted_risks else "None identified."

        user_content_parts = [
            f"PRIMARY GOAL:\n{goal}\n",
            f"YOUTH ADVERSARIAL RISK LOG:\n{risk_context}\n",
        ]

        if is_revision and elder_instructions:
            user_content_parts.append(
                f"ELDER AUDIT REJECTION & REWORKING INSTRUCTIONS:\n{elder_instructions}\n"
            )

        user_content_parts.append(
            "Synthesize architecture and write complete production implementation code addressing all requirements, risks, and visual reference images."
        )
        user_message = "\n".join(user_content_parts)

        # Call LLM
        resp = await self._invoke_llm(
            system_prompt=system_prompt,
            user_message=user_message,
            images=images,
            temperature=0.35,
        )

        data = extract_json_payload(resp.content)
        return self._build_output(data, resp, loop_index)

    def _build_output(
        self,
        data: Dict[str, Any],
        resp: Any,
        loop_index: int,
    ) -> PeerDraftOutput:
        import json
        overview = data.get("architecture_overview", "Synthesized architecture plan.")
        code_dict = data.get("implementation_code", {})
        if not isinstance(code_dict, dict):
            code_dict = {"main.py": str(code_dict)}

        # Extract nested metadata if LLM placed them inside implementation_code
        clean_code: Dict[str, str] = {}
        nested_mitigations: List[str] = []
        nested_assumptions: List[str] = []

        for k, v in code_dict.items():
            if k == "mitigations_applied":
                if isinstance(v, list):
                    nested_mitigations.extend(str(item) for item in v)
                elif v:
                    nested_mitigations.append(str(v))
            elif k == "assumptions_made":
                if isinstance(v, list):
                    nested_assumptions.extend(str(item) for item in v)
                elif v:
                    nested_assumptions.append(str(v))
            elif k == "architecture_overview" and isinstance(v, str):
                if not overview or overview == "Synthesized architecture plan.":
                    overview = v
            else:
                if isinstance(v, list):
                    clean_code[k] = "\n".join(str(item) for item in v)
                elif isinstance(v, dict):
                    clean_code[k] = json.dumps(v, indent=2)
                else:
                    clean_code[k] = str(v)

        mitigations = data.get("mitigations_applied", [])
        if not isinstance(mitigations, list):
            mitigations = [str(mitigations)] if mitigations else []
        mitigations.extend(nested_mitigations)

        assumptions = data.get("assumptions_made", [])
        if not isinstance(assumptions, list):
            assumptions = [str(assumptions)] if assumptions else []
        assumptions.extend(nested_assumptions)

        return PeerDraftOutput(
            agent_id=self.agent_id,
            loop_index=loop_index,
            architecture_overview=str(overview),
            implementation_code=clean_code,
            mitigations_applied=mitigations,
            assumptions_made=assumptions,
            tool_calls=[],
            input_tokens=resp.prompt_tokens,
            output_tokens=resp.completion_tokens,
            tokens_used=resp.total_tokens,
        )
