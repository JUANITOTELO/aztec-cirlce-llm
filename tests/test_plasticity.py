"""
Tests for the neuroplasticity subsystem: synaptic weight adaptation,
homeostatic thresholds, dynamic model routing, experience memory,
the PlasticityEngine facade, and orchestrator integration.
"""

from __future__ import annotations

import json

import pytest

from aztec_circle.config import settings
from aztec_circle.domain.models import (
    CircleRunState,
    ElderVerdict,
    VerdictStatus,
)
from aztec_circle.engine.budget_manager import BudgetManager
from aztec_circle.engine.consensus import ConsensusEngine
from aztec_circle.engine.state_machine import AztecOrchestrator
from aztec_circle.plasticity import PlasticityEngine
from aztec_circle.plasticity.homeostasis import HomeostaticThresholds
from aztec_circle.plasticity.memory import ExperienceMemory, _category_key
from aztec_circle.plasticity.router import DynamicModelRouter, score_complexity
from aztec_circle.plasticity.synaptic import SynapticWeightAdapter

from tests.conftest import MockLLMProvider


# ─────────────────────────────────────────────────────────────────────────────
# Synaptic weights
# ─────────────────────────────────────────────────────────────────────────────

class TestSynapticWeights:
    def test_initial_state_matches_baseline(self):
        adapter = SynapticWeightAdapter()
        snap = adapter.snapshot()
        assert abs(snap["security_governance"] - 0.6) < 0.01
        assert abs(snap["structural_perf"] - 0.4) < 0.01
        assert abs(sum(snap.values()) - 1.0) < 1e-6

    def test_reliable_auditor_gains_weight(self):
        adapter = SynapticWeightAdapter(learning_rate=0.5)
        before = adapter.snapshot()["security_governance"]
        # Security elder perfectly aligned with outcome for many runs.
        for _ in range(10):
            adapter.reinforce({"security_governance": 1.0, "structural_perf": 0.0})
        after = adapter.snapshot()
        assert after["security_governance"] > before
        assert after["structural_perf"] < 0.4 + 0.05
        assert abs(sum(after.values()) - 1.0) < 1e-3

    def test_weights_respect_bounds(self):
        adapter = SynapticWeightAdapter(learning_rate=1.0, min_weight=0.25, max_weight=0.7)
        for _ in range(200):
            adapter.reinforce({"security_governance": 1.0, "structural_perf": 1.0})
        snap = adapter.snapshot()
        assert all(v >= 0.25 - 1e-6 for v in snap.values())
        assert all(v <= 0.70 + 1e-6 for v in snap.values())
        assert abs(sum(snap.values()) - 1.0) < 1e-3

    def test_decay_pulls_toward_baseline_on_neutral_runs(self):
        adapter = SynapticWeightAdapter(decay=0.2)
        # Push far away...
        for _ in range(30):
            adapter.reinforce({"security_governance": 0.0, "structural_perf": 1.0})
        drifted = adapter.snapshot()["security_governance"]
        # ...then many runs where this persona is absent from signals.
        for _ in range(60):
            adapter.reinforce({})
        recovered = adapter.snapshot()["security_governance"]
        baseline = 0.6
        assert abs(recovered - baseline) < abs(drifted - baseline)

    def test_consensus_weights_export_both_key_forms(self):
        adapter = SynapticWeightAdapter()
        weights = adapter.consensus_weights()
        assert "security_governance" in weights
        assert "elder_security_governance" in weights
        assert weights["security_governance"] == pytest.approx(
            weights["elder_security_governance"]
        )

    def test_load_state_roundtrip_and_save_file(self, tmp_path):
        state_path = tmp_path / "plasticity.json"
        engine = PlasticityEngine(state_path=str(state_path), memory_db_path=str(tmp_path / "m.db"))
        engine.synaptic.reinforce({"security_governance": 1.0, "structural_perf": 0.0})
        engine.save_state()

        reloaded = PlasticityEngine(state_path=str(state_path), memory_db_path=str(tmp_path / "m.db"))
        assert reloaded.synaptic.snapshot() == engine.synaptic.snapshot()


# ─────────────────────────────────────────────────────────────────────────────
# Homeostasis
# ─────────────────────────────────────────────────────────────────────────────

class TestHomeostasis:
    def test_first_pass_approval_relaxes_threshold(self):
        h = HomeostaticThresholds(base_threshold=8.0, step=0.15)
        h.record_run(approved=True, loops_used=0, max_loops=2)
        assert h.approval_threshold == pytest.approx(8.0 - 0.15)

    def test_escalation_tightens_threshold(self):
        h = HomeostaticThresholds(base_threshold=8.0, step=0.15)
        h.record_run(approved=False, loops_used=2, max_loops=2)
        assert h.approval_threshold > 8.0

    def test_threshold_clamped_to_band(self):
        h = HomeostaticThresholds(base_threshold=8.0, floor=7.5, ceiling=8.4, step=0.5)
        for _ in range(10):
            h.record_run(approved=True, loops_used=0, max_loops=2)
        assert h.approval_threshold >= 7.5
        for _ in range(20):
            h.record_run(approved=False, loops_used=2, max_loops=2)
            # tighten step is amplified up to 3x per run but must stay bounded
        assert h.approval_threshold <= 8.4

    def test_flaw_recurrence_multiplier_bounded(self):
        h = HomeostaticThresholds()
        for _ in range(50):
            h.record_flaw_recurrence(1.0)
        assert h.flaw_recurrence_multiplier <= 1.5
        for _ in range(50):
            h.record_flaw_recurrence(0.0)
        assert h.flaw_recurrence_multiplier >= 1.0

    def test_recurring_flaws_raise_penalty_pct(self):
        h = HomeostaticThresholds()
        base = h.flaw_penalty_pct
        for _ in range(10):
            h.record_flaw_recurrence(0.9)
        assert h.flaw_penalty_pct > base

    def test_load_state_clamps_garbage(self):
        h = HomeostaticThresholds(floor=7.0, ceiling=9.0)
        h.load_state({"approval_threshold": 99.0, "flaw_recurrence_multiplier": -3.0})
        assert h.approval_threshold <= 9.0
        assert h.flaw_recurrence_multiplier >= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Dynamic routing
# ─────────────────────────────────────────────────────────────────────────────

class TestRouting:
    def test_low_complexity_routes_light_tier(self):
        router = DynamicModelRouter()
        plan = router.plan("fix typo in readme", image_count=0)
        assert plan.tier == "light"
        assert plan.peer == router.light_peer_model
        assert not plan.peer_escalated

    def test_moderate_complexity_routes_standard_tier(self):
        router = DynamicModelRouter(complexity_light_threshold=0.5)
        plan = router.plan("Build a small REST API with two endpoints")
        assert plan.tier in ("standard", "light")

    def test_high_complexity_routes_strong_tier(self):
        router = DynamicModelRouter()
        goal = (
            "Build a realtime websocket streaming dashboard with oauth authentication, "
            "postgres migrations, kubernetes deployment and a webgl 3d visualization parser"
        )
        plan = router.plan(goal)
        assert plan.complexity_score >= router.complexity_strong_threshold
        assert plan.tier == "strong"
        assert plan.peer == router.escalation_peer_model
        assert plan.peer_escalated

    def test_images_raise_complexity(self):
        plain = score_complexity("make a website", image_count=0)
        with_imgs = score_complexity("make a website", image_count=3)
        assert with_imgs > plain

    def test_stress_escalation_switches_peer_model(self):
        router = DynamicModelRouter()
        plan = router.plan("simple todo list app")
        assert not plan.peer_escalated
        router.escalate_peer(plan, "loop 1 rejected (score 6.2)")
        assert plan.peer_escalated
        assert plan.peer == router.escalation_peer_model
        assert any("Escalation" in n for n in plan.notes)

    def test_escalation_idempotent_at_top_tier(self):
        router = DynamicModelRouter()
        plan = router.plan("realtime distributed kubernetes parser", image_count=3)
        assert plan.peer == router.escalation_peer_model
        router.escalate_peer(plan, "loop 2 rejected")
        assert plan.peer == router.escalation_peer_model

    def test_budget_degradation_ladder(self):
        goal = "realtime oauth streaming platform"

        low_router = DynamicModelRouter()
        low = low_router.degrade_for_budget(low_router.plan(goal), 0.5)
        assert low.tier != "degraded"

        # At moderate pressure only the cheaper elder degrades.
        mid_router = DynamicModelRouter()
        mid_plan = mid_router.plan(goal)
        original_elder = mid_plan.elder_security
        mid = mid_router.degrade_for_budget(mid_plan, 0.75)

        high_router = DynamicModelRouter()
        high = high_router.degrade_for_budget(high_router.plan(goal), 0.95)
        assert high.elder_security == high_router.standard_peer_model
        assert high.elder_structural == high_router.standard_peer_model
        if high.peer_escalated:
            # ≥0.90 pressure reverts escalated peer to standard tier.
            assert high.peer == high_router.standard_peer_model


# ─────────────────────────────────────────────────────────────────────────────
# Experience memory
# ─────────────────────────────────────────────────────────────────────────────

class TestExperienceMemory:
    @pytest.fixture
    def memory(self, tmp_path):
        mem = ExperienceMemory(str(tmp_path / "exp.db"))
        yield mem
        mem.close()

    def test_category_key_is_stable_across_paraphrase_noise(self):
        _, h1 = _category_key("SQL Injection possible in login endpoint!!!")
        _, h2 = _category_key("sql injection possible in login endpoint")
        assert h1 == h2

    def test_record_run_updates_stats(self, memory):
        memory.record_run("t1", "goal", "APPROVED", loops_used=1, final_score=9.0,
                          cost_usd=0.05, total_tokens=1500)
        stats = memory.stats()
        assert stats["total_runs"] == 1
        assert stats["avg_final_score"] == pytest.approx(9.0)

    def test_recurring_flaws_detected_and_ranked(self, memory):
        flaw = "Privilege escalation possible in handler"
        for i in range(3):
            memory.record_run(f"t{i}", "goal", "ESCALATED_BEST_EFFORT", 1, 5.0, 0.1, 100)
            memory.record_flaws(f"t{i}", [flaw], ["Enforce role checks"])
        top = memory.top_recurring_flaws(limit=3)
        assert len(top) >= 1
        assert top[0]["occurrences"] == 3

    def test_insights_require_recurrence(self, memory):
        assert memory.insights_for_goal() is None  # empty DB
        memory.record_run("t1", "g", "REJECTED", 0, 5.0, 0.02, 300)
        memory.record_flaws("t1", ["One-off oddity"], [])
        assert memory.insights_for_goal() is None  # single occurrence = noise

        # The same flaw recurring across runs becomes a lesson.
        for task in ("t2", "t3"):
            memory.record_run(task, "g", "REJECTED", 1, 5.0, 0.02, 300)
            memory.record_flaws(task, ["Recurring XSS sink in template renderer"], ["Escape output"])
        text = memory.insights_for_goal()
        assert text is not None
        assert "INSTITUTIONAL MEMORY" in text
        assert "Recurring XSS sink" in text
        assert "Escape output" in text

    def test_known_hashes_snapshot_before_insert(self, memory):
        assert memory.known_category_hashes() == set()
        memory.record_flaws("t1", ["Flaw A"], [])
        hashes = memory.known_category_hashes()
        assert len(hashes) == 1

    def test_first_pass_approval_rate(self, memory):
        memory.record_run("a", "g", "APPROVED", loops_used=0, final_score=9, cost_usd=0, total_tokens=0)
        memory.record_run("b", "g", "APPROVED", loops_used=0, final_score=9, cost_usd=0, total_tokens=0)
        memory.record_run("c", "g", "ESCALATED_BEST_EFFORT", loops_used=2, final_score=5, cost_usd=0, total_tokens=0)
        rate = memory.first_pass_approval_rate(window=3)
        assert rate == pytest.approx(round(2 / 3, 3))

    def test_reset_clears_everything(self, memory):
        memory.record_run("t", "g", "APPROVED", 0, 9, 0, 0)
        memory.reset()
        assert memory.stats()["total_runs"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# PlasticityEngine facade
# ─────────────────────────────────────────────────────────────────────────────

def _verdict(agent_id: str, persona: str, score: float, flaws=None, instructions=None):
    return ElderVerdict(
        agent_id=agent_id,
        persona=persona,
        status=VerdictStatus.REJECTED if flaws else VerdictStatus.APPROVED,
        weighted_score=score,
        critical_flaws=flaws or [],
        reworking_instructions=instructions,
    )


class TestPlasticityEngine:
    @pytest.fixture
    def engine(self, tmp_path):
        eng = PlasticityEngine(
            state_path=str(tmp_path / "state.json"),
            memory_db_path=str(tmp_path / "mem.db"),
        )
        yield eng

    def test_disabled_engine_writes_nothing(self, tmp_path):
        eng = PlasticityEngine(
            state_path=str(tmp_path / "s.json"),
            memory_db_path=str(tmp_path / "m.db"),
            enabled=False,
        )
        eng.on_run_start("goal")
        eng.on_run_complete("t", "goal", "APPROVED", 1, 9.0, 0.01, 100)
        eng.save_state()
        assert not (tmp_path / "s.json").exists()

    def test_run_start_produces_routing_plan(self, engine):
        plan = engine.on_run_start("Build a complex realtime auth system")
        assert plan.peer
        assert engine._current_plan is plan

    def test_loop_rejection_escalates_only_after_first_loop(self, engine):
        engine.on_run_start("small app")
        original_peer = engine._current_plan.peer

        same = engine.on_loop_rejected(0, _verdict("e", "structural_perf", 6.0))
        assert same.peer == original_peer  # loop 0 rejection: no escalation yet

        escalated = engine.on_loop_rejected(1, _verdict("e", "structural_perf", 6.0))
        assert escalated.peer != original_peer or escalated.peer_escalated

    def test_run_complete_updates_all_subsystems(self, engine):
        engine.on_run_start("Build a caching layer")

        verdicts = [
            _verdict("elder_security_governance", "security_governance", 5.0,
                     flaws=["SQL injection in query builder"],
                     instructions="Parameterize queries"),
            _verdict("elder_structural_perf", "structural_perf", 8.5),
        ]
        consolidated = _verdict("consensus", "arbitrator", 6.0,
                                flaws=["SQL injection in query builder"])

        snapshot = engine.on_run_complete(
            task_id="task-1",
            goal="Build a caching layer",
            status="ESCALATED_HUMAN_IN_THE_LOOP",
            loops_used=2,
            final_score=6.0,
            cost_usd=0.42,
            total_tokens=4200,
            verdicts=verdicts,
            consolidated=consolidated,
        )

        # Memory recorded the run + flaws
        assert snapshot["memory_stats"]["total_runs"] == 1
        assert snapshot["memory_stats"]["flaw_events"] >= 1
        # Rejected run tightened the gate
        assert snapshot["homeostasis"]["approval_threshold"] > settings.PLASTICITY_BASE_THRESHOLD
        # Vigilant elder (flagged the flaw) reinforced vs. the one that missed it
        weights = snapshot["synaptic_weights"]
        assert weights["security_governance"] >= weights["structural_perf"]

    def test_approved_first_pass_relaxes_gate(self, engine):
        engine.on_run_start("tiny script")
        before = engine.homeostasis.approval_threshold
        engine.on_run_complete("t", "tiny script", "APPROVED", 1, 9.2, 0.01, 900,
                               verdicts=[], consolidated=_verdict("c", "arbitrator", 9.2))
        assert engine.homeostasis.approval_threshold < before

    def test_state_survives_process_restart(self, tmp_path):
        sp, mp = str(tmp_path / "s.json"), str(tmp_path / "m.db")
        e1 = PlasticityEngine(state_path=sp, memory_db_path=mp)
        e1.on_run_start("goal one")
        e1.on_run_complete("t", "goal one", "APPROVED", 1, 9.0, 0.01, 500)
        threshold_after_run1 = e1.homeostasis.approval_threshold

        e2 = PlasticityEngine(state_path=sp, memory_db_path=mp)
        assert e2.homeostasis.approval_threshold == pytest.approx(threshold_after_run1)
        assert e2.memory.stats()["total_runs"] == 1  # SQLite persists too

    def test_reset_restores_fresh_state(self, engine):
        engine.on_run_start("g")
        engine.on_run_complete("t", "g", "APPROVED", 1, 9, 0, 0)
        engine.reset()
        snap = engine.snapshot()
        assert snap["memory_stats"]["total_runs"] == 0
        assert snap["synaptic_weights"]["security_governance"] == pytest.approx(0.6, abs=0.01)

    def test_reliability_signals_rejected_run(self, engine):
        signals = engine._reliability_signals(
            [_verdict("elder_security_governance", "security_governance", 5.0,
                      flaws=["flaw"])],
            consolidated=_verdict("c", "arbitrator", 5.0, flaws=["flaw"]),
            approved=False,
        )
        assert 0.0 <= signals["security_governance"] <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Bridges: budget pressure + consensus live tuning
# ─────────────────────────────────────────────────────────────────────────────

class TestBridges:
    def test_budget_pressure_curve(self):
        bm = BudgetManager(limit_usd=1.0)
        assert bm.pressure() == 0.0
        bm.total_cost_usd = 0.5
        assert bm.pressure() == pytest.approx(0.5)
        bm.total_cost_usd = 5.0
        assert bm.pressure() == 1.0
        bm.limit_usd = 0
        assert bm.pressure() == 1.0

    def test_consensus_update_params_live(self):
        engine = ConsensusEngine()
        engine.update_params(approval_threshold=7.5, weights={"structural_perf": 0.9},
                             flaw_penalty_pct=0.2)
        assert engine.approval_threshold == 7.5
        assert engine.weights["structural_perf"] == 0.9
        assert engine.flaw_penalty_pct == 0.2


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator integration (mocked LLM providers)
# ─────────────────────────────────────────────────────────────────────────────

YOUTH_JSON = json.dumps({
    "radical_ideas": [], "identified_risks": [],
    "adversarial_scenarios": [], "override_triggered": False,
})
PEER_JSON = json.dumps({
    "architecture_overview": "Draft", "implementation_code": {"main.py": "print('x')"},
    "mitigations_applied": [], "assumptions_made": [],
})
ELDER_REJECT_JSON = json.dumps({
    "status": "REJECTED", "weighted_score": 5.0, "audit_items": [],
    "critical_flaws": ["Unresolved deadlock in scheduler"],
    "reworking_instructions": "Refactor the scheduler",
})
ELDER_APPROVE_JSON = json.dumps({
    "status": "APPROVED", "weighted_score": 9.0, "audit_items": [],
    "critical_flaws": [], "reworking_instructions": None,
})


class CircleMockProvider(MockLLMProvider):
    """
    Dispatches by rank marker found in the system prompt. Elder audits are
    REJECTED for the first `reject_first` calls, APPROVED afterwards.
    Records whether institutional memory reached the drafter.
    """

    def __init__(self, reject_first: int = 0):
        super().__init__()
        self.reject_first = reject_first
        self.elder_calls = 0
        self.saw_memory_injection = False
        self.models_seen: list[str] = []

    async def complete(self, messages, model=None, temperature=0.7,
                       thinking_budget=None, **kwargs):
        system = next((m["content"] for m in messages if m.get("role") == "system"), "")
        user = next((m["content"] for m in messages if m.get("role") == "user"), "")
        self.calls.append({"messages": messages, "model": model})

        if "Chaos Brainstormer" in system or "Devil's Advocate" in system:
            content = YOUTH_JSON
        elif "Code Drafter" in system:
            if "INSTITUTIONAL MEMORY" in user:
                self.saw_memory_injection = True
            self.models_seen.append(model or "?")
            content = PEER_JSON
        else:
            self.elder_calls += 1
            content = ELDER_REJECT_JSON if self.elder_calls <= self.reject_first * 2 \
                else ELDER_APPROVE_JSON

        return LLMResponse(content=content, prompt_tokens=100, completion_tokens=50,
                           total_tokens=150, model=model or "mock")


@pytest.mark.asyncio
async def test_orchestrator_full_run_with_plasticity(temp_db_path, tmp_path):
    """Happy path: routing applied, run completes, learning persisted."""
    provider = CircleMockProvider(reject_first=0)
    from aztec_circle.engine.checkpoint import CheckpointStore as CS
    store = CS(db_path=temp_db_path)

    engine = PlasticityEngine(
        state_path=str(tmp_path / "p.json"),
        memory_db_path=str(tmp_path / "e.db"),
    )
    y1 = YouthAgent(persona="chaos_brainstormer", provider=provider)
    y2 = YouthAgent(persona="devils_advocate", provider=provider)
    peer = PeerAgent(provider=provider)
    e1 = ElderAgent(persona="security_governance", provider=provider)
    e2 = ElderAgent(persona="structural_perf", provider=provider)

    orch = AztecOrchestrator(
        state=CircleRunState(goal="Build a simple utility"),
        checkpoint_store=store,
        youth_agents=[y1, y2],
        peer_agent=peer,
        elder_agents=[e1, e2],
        plasticity=engine,
    )
    result = await orch.run()

    assert result["status"] == "APPROVED"
    assert engine.memory.stats()["total_runs"] == 1
    assert (tmp_path / "p.json").exists()  # learned state persisted


@pytest.mark.asyncio
async def test_orchestrator_rejection_triggers_adaptation(temp_db_path, tmp_path):
    """Second consecutive rejection escalates the peer model tier mid-run."""
    from aztec_circle.engine.checkpoint import CheckpointStore as CS

    provider = CircleMockProvider(reject_first=2)
    store = CS(db_path=temp_db_path)
    engine = PlasticityEngine(
        state_path=str(tmp_path / "p.json"),
        memory_db_path=str(tmp_path / "e.db"),
    )

    y1 = YouthAgent(persona="chaos_brainstormer", provider=provider)
    y2 = YouthAgent(persona="devils_advocate", provider=provider)
    peer = PeerAgent(provider=provider)
    e1 = ElderAgent(persona="security_governance", provider=provider)
    e2 = ElderAgent(persona="structural_perf", provider=provider)

    orch = AztecOrchestrator(
        state=CircleRunState(goal="Build a moderately complex api service", max_loops=3),
        checkpoint_store=store,
        youth_agents=[y1, y2],
        peer_agent=peer,
        elder_agents=[e1, e2],
        plasticity=engine,
    )
    # Routing normally skips injected agents; lift the guard so we can observe
    # stress escalation on the live peer agent.
    orch._agents_injected = False
    initial_peer_model = peer.model

    result = await orch.run()

    assert result["status"] == "APPROVED"          # approved on loop 2
    assert provider.elder_calls == 6               # 2 elders x 3 loops
    assert engine._current_plan is not None
    assert engine._current_plan.peer_escalated     # stress response fired
    assert peer.model != initial_peer_model        # live agent re-routed
    # Escalation is recorded in memory: run completed with tier info
    assert engine.memory.stats()["total_runs"] == 1


@pytest.mark.asyncio
async def test_orchestrator_memory_reaches_drafter_on_second_run(temp_db_path, tmp_path):
    """Institutional memory recorded in run 1 is injected into run 2's draft prompt."""
    from aztec_circle.engine.checkpoint import CheckpointStore as CS

    sp, mp = str(tmp_path / "p.json"), str(tmp_path / "e.db")

    def build_orchestrator():
        provider = CircleMockProvider(reject_first=1)
        orch = AztecOrchestrator(
            state=CircleRunState(goal="Build the recurring deadlock scheduler app"),
            checkpoint_store=CS(db_path=temp_db_path),
            youth_agents=[
                YouthAgent(persona="chaos_brainstormer", provider=provider),
                YouthAgent(persona="devils_advocate", provider=provider),
            ],
            peer_agent=PeerAgent(provider=provider),
            elder_agents=[
                ElderAgent(persona="security_governance", provider=provider),
                ElderAgent(persona="structural_perf", provider=provider),
            ],
            plasticity=PlasticityEngine(state_path=sp, memory_db_path=mp),
        )
        return orch, provider

    orch1, provider1 = build_orchestrator()
    await orch1.run()
    assert provider1.saw_memory_injection is False  # nothing learned yet

    orch2, provider2 = build_orchestrator()
    await orch2.run()
    assert provider2.saw_memory_injection is True   # lesson learned in run 1


@pytest.mark.asyncio
async def test_orchestrator_plasticity_failure_never_breaks_run(temp_db_path, tmp_path):
    """A broken plasticity engine degrades to vanilla circle behavior."""

    class ExplodingEngine:
        enabled = True

        def __getattr__(self, name):
            raise RuntimeError("plasticity exploded")

    from typing import Any, cast

    from aztec_circle.engine.checkpoint import CheckpointStore as CS

    provider = CircleMockProvider(reject_first=0)
    y1 = YouthAgent(persona="chaos_brainstormer", provider=provider)
    y2 = YouthAgent(persona="devils_advocate", provider=provider)

    orch = AztecOrchestrator(
        state=CircleRunState(goal="Simple task"),
        checkpoint_store=CS(db_path=temp_db_path),
        youth_agents=[y1, y2],
        peer_agent=PeerAgent(provider=provider),
        elder_agents=[
            ElderAgent(persona="security_governance", provider=provider),
            ElderAgent(persona="structural_perf", provider=provider),
        ],
        plasticity=cast(Any, ExplodingEngine()),
    )
    result = await orch.run()
    assert result["status"] == "APPROVED"


# Imports used by integration tests above (kept at bottom to keep the unit
# sections readable); flake8-style placement is deliberate for test clarity.
from aztec_circle.agents.elder import ElderAgent  # noqa: E402
from aztec_circle.agents.peer import PeerAgent  # noqa: E402
from aztec_circle.agents.youth import YouthAgent  # noqa: E402
from aztec_circle.adapters.llm_provider import LLMResponse  # noqa: E402
from aztec_circle.engine.checkpoint import CheckpointStore  # noqa: E402,F401
