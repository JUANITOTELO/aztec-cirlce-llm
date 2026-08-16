"""
Tests for domain models, validation, and serialization.
"""

from aztec_circle.domain.models import (
    AgentRank,
    CirclePhase,
    CircleRunState,
    ElderAuditItem,
    ElderVerdict,
    FallbackPolicy,
    PeerDraftOutput,
    SeverityLevel,
    VerdictStatus,
    YouthBrainstormOutput,
    YouthRiskItem,
)


def test_agent_rank_and_phases():
    assert AgentRank.YOUTH == "YOUTH"
    assert AgentRank.PEER == "PEER"
    assert AgentRank.ELDER == "ELDER"
    assert CirclePhase.IDLE == "IDLE"
    assert CirclePhase.RESOLVED == "RESOLVED"
    assert CirclePhase.EMERGENCY_HALTED == "EMERGENCY_HALTED"


def test_youth_risk_item_defaults():
    item = YouthRiskItem(
        category="security",
        description="SQL injection vulnerability",
        severity=SeverityLevel.HIGH,
        suggested_mitigation="Use parameterized queries",
    )
    assert len(item.id) == 8
    assert item.is_showstopper is False
    assert item.severity == SeverityLevel.HIGH


def test_circle_run_state_serialization():
    state = CircleRunState(
        goal="Build an in-memory cache",
        budget_limit_usd=2.50,
        max_loops=3,
        fallback_policy=FallbackPolicy.BEST_EFFORT_RELEASE,
    )
    json_str = state.model_dump_json()
    assert "in-memory cache" in json_str

    deserialized = CircleRunState.model_validate_json(json_str)
    assert deserialized.task_id == state.task_id
    assert deserialized.goal == state.goal
    assert deserialized.budget_limit_usd == 2.50
    assert deserialized.max_loops == 3
    assert deserialized.fallback_policy == FallbackPolicy.BEST_EFFORT_RELEASE


def test_elder_audit_item_constraints():
    audit = ElderAuditItem(
        criterion="Security",
        weight=0.5,
        score=8.5,
        critique="Good isolation",
        passed=True,
    )
    assert audit.score == 8.5
    assert audit.weight == 0.5
