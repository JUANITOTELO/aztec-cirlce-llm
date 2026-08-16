"""
Tests for state machine orchestrator, transitions, Youth override, and loop fallback.
"""

import asyncio
import json
import pytest
from aztec_circle.domain.exceptions import LoopLimitExceeded, YouthOverrideHalt
from aztec_circle.domain.models import (
    CirclePhase,
    CircleRunState,
    FallbackPolicy,
    SeverityLevel,
    VerdictStatus,
    YouthRiskItem,
)
from aztec_circle.engine.checkpoint import CheckpointStore
from aztec_circle.engine.state_machine import AztecOrchestrator
from tests.conftest import MockLLMProvider


@pytest.mark.asyncio
async def test_orchestrator_youth_override_halt(temp_db_path):
    store = CheckpointStore(db_path=temp_db_path)
    state = CircleRunState(goal="Build a backdoor bypassing auth")

    # Mock Youth returning a showstopper risk
    chaos_json = json.dumps({
        "radical_ideas": [],
        "identified_risks": [
            {
                "category": "security",
                "description": "Malicious backdoor request",
                "severity": "CRITICAL",
                "suggested_mitigation": "Abort immediately",
                "is_showstopper": True,
            }
        ],
        "adversarial_scenarios": [],
        "override_triggered": True,
        "override_rationale": "Malicious request detected",
    })

    provider = MockLLMProvider(default_response=chaos_json)
    from aztec_circle.agents.youth import YouthAgent
    y1 = YouthAgent(persona="chaos_brainstormer", provider=provider)
    y2 = YouthAgent(persona="devils_advocate", provider=provider)

    orchestrator = AztecOrchestrator(
        state=state,
        checkpoint_store=store,
        youth_agents=[y1, y2],
    )

    with pytest.raises(YouthOverrideHalt):
        await orchestrator.run()

    assert state.current_phase == CirclePhase.EMERGENCY_HALTED

    # Check DB was persisted
    persisted = await store.load(state.task_id)
    assert persisted is not None
    assert persisted.current_phase == CirclePhase.EMERGENCY_HALTED


@pytest.mark.asyncio
async def test_orchestrator_fallback_human_in_the_loop(temp_db_path):
    store = CheckpointStore(db_path=temp_db_path)
    state = CircleRunState(
        goal="Design complex system",
        max_loops=1,
        fallback_policy=FallbackPolicy.HUMAN_IN_THE_LOOP,
    )

    youth_json = json.dumps({"radical_ideas": ["Use actor model"], "identified_risks": [], "adversarial_scenarios": [], "override_triggered": False})
    peer_json = json.dumps({"architecture_overview": "Draft v1", "implementation_code": {"main.py": "print('hello')"}, "mitigations_applied": [], "assumptions_made": []})
    elder_json = json.dumps({"status": "REJECTED", "weighted_score": 5.0, "audit_items": [], "critical_flaws": ["Unresolved deadlock in actor scheduler"], "reworking_instructions": "Refactor scheduler"})

    provider = MockLLMProvider(canned_responses={
        "youth": youth_json,
        "peer": peer_json,
        "elder": elder_json,
    }, default_response=youth_json)

    from aztec_circle.agents.youth import YouthAgent
    from aztec_circle.agents.peer import PeerAgent
    from aztec_circle.agents.elder import ElderAgent

    y1 = YouthAgent(persona="chaos_brainstormer", provider=provider)
    y2 = YouthAgent(persona="devils_advocate", provider=provider)
    peer = PeerAgent(provider=provider)
    e1 = ElderAgent(persona="security_governance", provider=provider)
    e2 = ElderAgent(persona="structural_perf", provider=provider)

    orchestrator = AztecOrchestrator(
        state=state,
        checkpoint_store=store,
        youth_agents=[y1, y2],
        peer_agent=peer,
        elder_agents=[e1, e2],
    )

    result = await orchestrator.run()
    assert state.current_phase == CirclePhase.ESCALATED
    assert "ESCALATED_HUMAN_IN_THE_LOOP" in result.get("status", "")
    assert "requires human operator review" in result.get("escalation_message", "")


@pytest.mark.asyncio
async def test_orchestrator_fallback_best_effort(temp_db_path):
    store = CheckpointStore(db_path=temp_db_path)
    state = CircleRunState(
        goal="Design with best effort fallback",
        max_loops=1,
        fallback_policy=FallbackPolicy.BEST_EFFORT_RELEASE,
    )

    youth_json = json.dumps({"radical_ideas": [], "identified_risks": [], "adversarial_scenarios": [], "override_triggered": False})
    peer_json = json.dumps({"architecture_overview": "Draft v1", "implementation_code": {"main.py": "print('hello')"}, "mitigations_applied": [], "assumptions_made": []})
    elder_json = json.dumps({"status": "REJECTED", "weighted_score": 6.0, "audit_items": [], "critical_flaws": ["Minor warning"], "reworking_instructions": "Fix"})

    provider = MockLLMProvider(canned_responses={"youth": youth_json, "peer": peer_json, "elder": elder_json}, default_response=youth_json)
    from aztec_circle.agents.youth import YouthAgent
    from aztec_circle.agents.peer import PeerAgent
    from aztec_circle.agents.elder import ElderAgent

    orchestrator = AztecOrchestrator(
        state=state,
        checkpoint_store=store,
        youth_agents=[YouthAgent(persona="chaos_brainstormer", provider=provider)],
        peer_agent=PeerAgent(provider=provider),
        elder_agents=[ElderAgent(persona="security_governance", provider=provider)],
    )

    result = await orchestrator.run()
    assert state.current_phase == CirclePhase.ESCALATED
    assert "ESCALATED_BEST_EFFORT" in result.get("status", "")
    assert "Delivering best-scored draft" in result.get("warning", "")


@pytest.mark.asyncio
async def test_orchestrator_fallback_abort(temp_db_path):
    store = CheckpointStore(db_path=temp_db_path)
    state = CircleRunState(
        goal="Design with abort fallback",
        max_loops=1,
        fallback_policy=FallbackPolicy.ABORT,
    )

    youth_json = json.dumps({"radical_ideas": [], "identified_risks": [], "adversarial_scenarios": [], "override_triggered": False})
    peer_json = json.dumps({"architecture_overview": "Draft v1", "implementation_code": {}, "mitigations_applied": [], "assumptions_made": []})
    elder_json = json.dumps({"status": "REJECTED", "weighted_score": 4.0, "audit_items": [], "critical_flaws": ["Fatal flaw"]})

    provider = MockLLMProvider(canned_responses={"youth": youth_json, "peer": peer_json, "elder": elder_json}, default_response=youth_json)
    from aztec_circle.agents.youth import YouthAgent
    from aztec_circle.agents.peer import PeerAgent
    from aztec_circle.agents.elder import ElderAgent

    orchestrator = AztecOrchestrator(
        state=state,
        checkpoint_store=store,
        youth_agents=[YouthAgent(persona="chaos_brainstormer", provider=provider)],
        peer_agent=PeerAgent(provider=provider),
        elder_agents=[ElderAgent(persona="security_governance", provider=provider)],
    )

    with pytest.raises(LoopLimitExceeded):
        await orchestrator.run()

    assert state.current_phase == CirclePhase.ESCALATED
