"""
Consensus and arbitration engine for Elder Council verdicts.
"""

from __future__ import annotations

from typing import Dict, List, Optional
import structlog

from aztec_circle.domain.models import ElderVerdict, VerdictStatus

log = structlog.get_logger(__name__)

APPROVAL_THRESHOLD = 8.0
CRITICAL_FLAW_PENALTY = 2.5
DEFAULT_ELDER_WEIGHTS: Dict[str, float] = {
    "elder_security_governance": 0.60,
    "elder_structural_perf": 0.40,
    "security_governance": 0.60,
    "structural_perf": 0.40,
}


class ConsensusEngine:
    def __init__(
        self,
        approval_threshold: float = APPROVAL_THRESHOLD,
        flaw_penalty: float = CRITICAL_FLAW_PENALTY,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.approval_threshold = approval_threshold
        self.flaw_penalty = flaw_penalty
        self.weights = weights or DEFAULT_ELDER_WEIGHTS

    def arbitrate(self, verdicts: List[ElderVerdict]) -> ElderVerdict:
        """
        Compute weighted consensus of Elder verdicts and evaluate approval vs rework.
        """
        if not verdicts:
            return ElderVerdict(
                agent_id="consensus_arbitrator",
                persona="arbitrator",
                status=VerdictStatus.REJECTED,
                weighted_score=0.0,
                audit_items=[],
                critical_flaws=["No elder verdicts provided for arbitration"],
                reworking_instructions="Resubmit for full audit.",
            )

        weighted_score_sum = 0.0
        total_weight = 0.0
        all_flaws: List[str] = []
        rework_instructions: List[str] = []

        for v in verdicts:
            w = self.weights.get(v.agent_id, self.weights.get(v.persona, 1.0 / len(verdicts)))
            weighted_score_sum += w * v.weighted_score
            total_weight += w

            all_flaws.extend(v.critical_flaws)
            if v.reworking_instructions:
                rework_instructions.append(f"[{v.agent_id} / {v.persona}]\n{v.reworking_instructions}")

        raw_score = (weighted_score_sum / total_weight) if total_weight > 0 else 0.0

        # Unique critical flaws
        unique_flaws = list(dict.fromkeys([f.strip() for f in all_flaws if f.strip()]))
        penalized_score = max(0.0, raw_score - (len(unique_flaws) * self.flaw_penalty))
        final_score = round(penalized_score, 2)

        approved = (final_score >= self.approval_threshold) and (len(unique_flaws) == 0)

        log.info(
            "consensus.arbitrated",
            verdict_count=len(verdicts),
            raw_score=round(raw_score, 2),
            final_score=final_score,
            flaw_count=len(unique_flaws),
            approved=approved,
        )

        return ElderVerdict(
            agent_id="consensus_arbitrator",
            persona="arbitrator",
            status=VerdictStatus.APPROVED if approved else VerdictStatus.REJECTED,
            weighted_score=final_score,
            audit_items=[],
            critical_flaws=unique_flaws,
            reworking_instructions="\n\n".join(rework_instructions) if rework_instructions else None,
        )
