"""
Tests for TUI UX: live event rendering (arbitration, plasticity, errors),
neuroplastic status surfaces (/status, /plasticity, welcome banner).
"""

from __future__ import annotations

import pytest
from rich.console import Console

from aztec_circle.tui.commands import dispatch_slash_command, cmd_status
from aztec_circle.tui.completer import SLASH_COMMAND_METADATA
from aztec_circle.tui.renderer import TranscriptRenderer, print_welcome_banner
from aztec_circle.tui.session import SessionState


def _render(event: dict) -> str:
    console = Console(record=True, width=200)
    renderer = TranscriptRenderer(console)
    renderer.render_event(event)
    return console.export_text()


# ── Live orchestrator events ─────────────────────────────────────────────────

def test_renders_arbitration_rejected_with_flaws():
    text = _render({
        "event": "arbitration.result",
        "loop": 1,
        "score": 6.42,
        "status": "REJECTED",
        "flaws": ["deadlock", "sql injection"],
    })
    assert "6.42/10" in text
    assert "2 critical flaw(s)" in text
    assert "REWORK REQUESTED" in text


def test_renders_arbitration_approved():
    text = _render({"event": "arbitration.result", "loop": 0, "score": 9.1, "status": "APPROVED", "flaws": []})
    assert "9.10/10" in text
    assert "APPROVED" in text


def test_renders_override_halt():
    text = _render({"event": "override.halt", "rationale": "Malicious request detected"})
    assert "OVERRIDE HALT" in text
    assert "Malicious request detected" in text


def test_renders_agent_errors():
    youth = _render({"event": "youth.error", "error": "timeout"})
    elder = _render({"event": "elder.error", "error": "rate limited"})
    assert "Youth agent error" in youth and "timeout" in youth
    assert "Elder agent error" in elder and "rate limited" in elder


def test_renders_resolved_and_escalated():
    resolved = _render({"event": "circle.resolved", "loop_count": 2, "total_cost_usd": 0.42})
    escalated = _render({
        "event": "circle.escalated",
        "status": "ESCALATED_BEST_EFFORT",
        "warning": "Max loops reached",
    })
    assert "Circle resolved" in resolved and "$0.4200" in resolved
    assert "ESCALATED_BEST_EFFORT" in escalated and "Max loops reached" in escalated


def test_phase_rule_for_new_phases_and_dedupe():
    console = Console(record=True, width=200)
    renderer = TranscriptRenderer(console)
    renderer.render_event({"event": "phase.change", "phase": "ELDER_AUDIT", "loop": 0, "cost_usd": 0.01})
    renderer.render_event({"event": "phase.change", "phase": "ELDER_AUDIT", "loop": 0, "cost_usd": 0.01})
    renderer.render_event({"event": "phase.change", "phase": "ARBITRATION", "loop": 0, "cost_usd": 0.01})
    text = console.export_text()
    assert "Elder Council" in text
    assert "Consensus & Arbitration" in text
    # Duplicate consecutive phase should render the rule only once.
    assert text.count("Elder Council") == text.count("Consensus & Arbitration")


def test_legacy_uppercase_events_still_render():
    verdict = _render({"event": "VERDICT_ISSUED", "auditor": "Security Elder", "approved": False, "score": 4.5})
    completed = _render({"event": "AGENT_COMPLETED", "agent_role": "Chaos Brainstormer", "tokens_used": 120, "cost_usd": 0.01})
    consensus = _render({"event": "CONSENSUS_REACHED", "approved": True, "score": 8.8, "flaw_count": 0})
    assert "Security Elder" in verdict and "REWORK REQUESTED" in verdict
    assert "Chaos Brainstormer" in completed
    assert "CONSENSUS APPROVED" in consensus


# ── Neuroplasticity events ───────────────────────────────────────────────────

def test_renders_plasticity_routing_event():
    text = _render({
        "event": "plasticity.routing",
        "tier": "strong",
        "complexity_score": 6.3,
        "peer": "gemini/gemini-2.5-pro",
        "memory_injected": True,
    })
    assert "Neuroplastic routing" in text
    assert "strong" in text
    assert "6.3" in text
    assert "institutional memory injected" in text


def test_renders_plasticity_adaptation_event():
    text = _render({
        "event": "plasticity.adapted",
        "loop": 1,
        "tier": "strong",
        "notes": ["Escalation: loop 1 rejected (score 5.5)"],
        "peer": "gemini/gemini-2.5-pro",
    })
    assert "Adapting under stress" in text
    assert "Escalation: loop 1 rejected" in text


def test_renders_plasticity_learning_summary():
    text = _render({
        "event": "plasticity.complete",
        "synaptic_weights": {"security_governance": 0.62, "structural_perf": 0.38},
        "homeostasis": {"approval_threshold": 8.15, "flaw_recurrence_multiplier": 1.05},
        "memory_stats": {"total_runs": 12},
    })
    assert "Learning updated" in text
    assert "approval gate 8.15" in text
    assert "12 run(s)" in text


# ── Welcome banner + slash command surfaces ──────────────────────────────────

def test_welcome_banner_shows_neuroplasticity_row():
    console = Console(record=True, width=220)
    print_welcome_banner(console, SessionState())
    text = console.export_text()
    assert "Neuroplasticity" in text


@pytest.mark.asyncio
async def test_cmd_status_includes_neuroplastic_section():
    from aztec_circle.config import settings

    if not settings.PLASTICITY_ENABLED:
        pytest.skip("plasticity disabled in this environment")
    console = Console(record=True, width=220)
    await cmd_status("", SessionState(), console)
    text = console.export_text()
    assert "Aztec Session Status" in text
    assert "Neuroplastic State" in text


@pytest.mark.asyncio
async def test_plasticity_command_snapshot_lessons_reset(tmp_path):
    from aztec_circle.config import settings

    if not settings.PLASTICITY_ENABLED:
        pytest.skip("plasticity disabled in this environment")

    from aztec_circle.plasticity import PlasticityEngine

    if not settings.PLASTICITY_ENABLED:
        pytest.skip("plasticity disabled in this environment")

    # Seed learning through the settings-isolated paths (same files the
    # slash command will read, thanks to the autouse isolation fixture).
    engine = PlasticityEngine()
    engine.on_run_start("goal")
    engine.on_run_complete(
        task_id="t1", goal="goal", status="APPROVED", loops_used=1,
        final_score=9.0, cost_usd=0.01, total_tokens=500,
    )
    engine.memory.record_flaws("t1", ["Recurring flaw A"], ["Fix A"])
    engine.memory.record_flaws("t1", ["Recurring flaw A"], ["Fix A"])
    engine.save_state()
    engine.memory.close()

    state = SessionState()

    # Snapshot view
    console = Console(record=True, width=220)
    await dispatch_slash_command("/plasticity", state, console)
    text = console.export_text()
    assert "Neuroplastic Engine" in text
    assert "Synaptic Weights" in text

    # Lessons view shows recurring flaw with its proven fix
    console = Console(record=True, width=220)
    await dispatch_slash_command("/plasticity lessons", state, console)
    text = console.export_text()
    assert "Lessons Learned" in text or "No flaw lessons" in text
    if "Lessons Learned" in text:
        assert "Recurring flaw A" in text
        assert "Fix A" in text

    # Reset wipes learned state
    console = Console(record=True, width=220)
    await dispatch_slash_command("/plasticity reset", state, console)
    text = console.export_text()
    assert "reset complete" in text.lower()

    fresh = PlasticityEngine()
    assert fresh.memory.stats()["total_runs"] == 0
    fresh.memory.close()


def test_completer_metadata_includes_plasticity():
    assert "/plasticity" in SLASH_COMMAND_METADATA
