"""
Tests for consensus engine, weighting, flaw penalties, and arbitration.
"""

from aztec_circle.domain.models import (
    ElderAuditItem,
    ElderVerdict,
    VerdictStatus,
)
from aztec_circle.engine.consensus import ConsensusEngine


def test_consensus_approval_when_both_pass():
    v1 = ElderVerdict(
        agent_id="elder_security_governance",
        persona="security_governance",
        status=VerdictStatus.APPROVED,
        weighted_score=9.0,
        critical_flaws=[],
    )
    v2 = ElderVerdict(
        agent_id="elder_structural_perf",
        persona="structural_perf",
        status=VerdictStatus.APPROVED,
        weighted_score=8.5,
        critical_flaws=[],
    )

    engine = ConsensusEngine()
    final_verdict = engine.arbitrate([v1, v2])

    assert final_verdict.status == VerdictStatus.APPROVED
    assert final_verdict.weighted_score >= 8.0
    assert len(final_verdict.critical_flaws) == 0


def test_consensus_rejection_with_critical_flaw():
    v1 = ElderVerdict(
        agent_id="elder_security_governance",
        persona="security_governance",
        status=VerdictStatus.REJECTED,
        weighted_score=5.0,
        critical_flaws=["Privilege escalation possible in handler"],
        reworking_instructions="Enforce token role validation",
    )
    v2 = ElderVerdict(
        agent_id="elder_structural_perf",
        persona="structural_perf",
        status=VerdictStatus.APPROVED,
        weighted_score=9.0,
        critical_flaws=[],
    )

    engine = ConsensusEngine()
    final_verdict = engine.arbitrate([v1, v2])

    assert final_verdict.status == VerdictStatus.REJECTED
    assert len(final_verdict.critical_flaws) == 1
    assert "Enforce token role" in final_verdict.reworking_instructions


def test_consensus_arbitration_empty_verdicts():
    engine = ConsensusEngine()
    verdict = engine.arbitrate([])
    assert verdict.status == VerdictStatus.REJECTED
    assert verdict.weighted_score == 0.0


def test_consensus_proportional_and_capped_flaw_penalty():
    # Test capped penalty with many flaws
    flaws = [f"Flaw {i}" for i in range(27)]
    v1 = ElderVerdict(
        agent_id="elder_security_governance",
        persona="security_governance",
        status=VerdictStatus.REJECTED,
        weighted_score=6.8,
        critical_flaws=flaws,
    )
    v2 = ElderVerdict(
        agent_id="elder_structural_perf",
        persona="structural_perf",
        status=VerdictStatus.REJECTED,
        weighted_score=6.8,
        critical_flaws=flaws,
    )
    engine = ConsensusEngine()
    verdict = engine.arbitrate([v1, v2])

    assert verdict.status == VerdictStatus.REJECTED
    # 27 flaws * 15% = 405%, capped at 60% -> 6.8 * (1 - 0.60) = 2.72
    assert verdict.weighted_score == 2.72
    assert len(verdict.critical_flaws) == 27

