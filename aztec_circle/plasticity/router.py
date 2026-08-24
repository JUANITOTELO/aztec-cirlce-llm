"""
Dynamic model router.

Routes each rank to a model tier based on measured task complexity, escalates
under stress (repeated rework), and degrades gracefully under budget pressure
instead of letting a run die against the hard budget breaker.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import structlog

from aztec_circle.config import settings

log = structlog.get_logger(__name__)

# Signals that correlate with hard generation problems.
_COMPLEXITY_PATTERNS = [
    (r"\b(realtime|real-time|websocket|webrtc|streaming)\b", 2.0),
    (r"\b(auth|oauth|jwt|encryption|crypto|security|permission)\b", 1.5),
    (r"\b(migrate|migration|schema|database|postgres|mysql|sqlite)\b", 1.5),
    (r"\b(optimi[sz]e|performance|scal(e|ing)|throughput|concurr\w+)\b", 1.5),
    (r"\b(distributed|microservice|kubernetes|docker|queue)\b", 2.0),
    (r"\b(parser|compiler|interpreter|grammar|ast)\b", 2.0),
    (r"\b(3d|webgl|shader|canvas|animation|physics)\b", 1.5),
    (r"\b(fullstack|full-stack|monorepo|architecture)\b", 1.0),
]


@dataclass
class RoutingPlan:
    """Resolved models for one run, per role."""
    youth_chaos: str
    youth_advocate: str
    peer: str
    elder_security: str
    elder_structural: str
    peer_escalated: bool = False
    complexity_score: float = 0.0
    tier: str = "standard"
    notes: List[str] = field(default_factory=list)

    def snapshot(self) -> Dict[str, object]:
        return {
            "youth_chaos": self.youth_chaos,
            "youth_advocate": self.youth_advocate,
            "peer": self.peer,
            "elder_security": self.elder_security,
            "elder_structural": self.elder_structural,
            "peer_escalated": self.peer_escalated,
            "complexity_score": round(self.complexity_score, 2),
            "tier": self.tier,
        }


def score_complexity(goal: str, image_count: int = 0) -> float:
    """
    Heuristic task-complexity score ∈ [0, ~10]. Cheap (regex only): computed
    once per run and reused for every routing decision.
    """
    text = (goal or "").lower()
    score = min(3.0, len(text) / 400.0)          # verbosity pressure
    pattern_hits = 0
    for pattern, weight in _COMPLEXITY_PATTERNS:
        if re.search(pattern, text):
            pattern_hits += 1
            score += weight * 0.6                # diminishing returns per hit
    # Many distinct domains => genuinely complex goal.
    if pattern_hits >= 4:
        score += 1.5
    score += 0.75 * min(3, image_count or 0)      # multimodal grounding cost
    return round(min(10.0, score), 2)


class DynamicModelRouter:
    """
    Tiered routing with stress escalation and budget-pressure degradation.

    Tiers are derived from configured rank baselines so nothing is hardcoded:
      light   : youth-tier models used for peer drafting on trivial tasks
      standard: configured baselines
      strong  : escalation models when complexity is high or loops fail
    """

    def __init__(
        self,
        escalation_peer_model: Optional[str] = None,
        complexity_strong_threshold: float = 5.0,
        complexity_light_threshold: float = 1.5,
    ):
        self.escalation_peer_model = (
            escalation_peer_model
            or getattr(settings, "PEER_ESCALATION_MODEL", None)
            or settings.get_effective_model("ELDER")
        )
        self.light_peer_model = settings.get_effective_model("YOUTH")
        self.standard_peer_model = settings.get_effective_model("PEER")
        self.complexity_strong_threshold = complexity_strong_threshold
        self.complexity_light_threshold = complexity_light_threshold

    def plan(self, goal: str, image_count: int = 0) -> RoutingPlan:
        complexity = score_complexity(goal, image_count=image_count)
        if complexity >= self.complexity_strong_threshold:
            tier = "strong"
            peer_model = self.escalation_peer_model
            note = f"High complexity ({complexity}) → strong tier"
        elif complexity <= self.complexity_light_threshold and not image_count:
            tier = "light"
            peer_model = self.light_peer_model
            note = f"Low complexity ({complexity}) → light tier"
        else:
            tier = "standard"
            peer_model = self.standard_peer_model
            note = f"Moderate complexity ({complexity}) → standard tier"

        plan = RoutingPlan(
            youth_chaos=settings.get_effective_model("YOUTH_CHAOS"),
            youth_advocate=settings.get_effective_model("YOUTH_ADVOCATE"),
            peer=peer_model,
            elder_security=settings.get_effective_model("ELDER_SECURITY"),
            elder_structural=settings.get_effective_model("ELDER_STRUCTURAL"),
            # Explicit tier flag: never infer from model identity, since configs
            # can legitimately alias multiple tiers to the same model.
            peer_escalated=(tier == "strong"),
            complexity_score=complexity,
            tier=tier,
            notes=[note],
        )
        log.info("router.plan", tier=tier, complexity=complexity, peer=peer_model)
        return plan

    def escalate_peer(self, plan: RoutingPlan, reason: str) -> RoutingPlan:
        """Stress-triggered escalation after rejected drafts."""
        if not plan.peer_escalated:
            plan.notes.append(f"Escalation: {reason}")
            plan.peer = self.escalation_peer_model
            plan.peer_escalated = True
            plan.tier = "strong"
            log.info("router.escalated", reason=reason, peer=plan.peer)
        else:
            plan.notes.append(f"Already at strongest tier; holding ({reason})")
        return plan

    def degrade_for_budget(self, plan: RoutingPlan, pressure: float) -> RoutingPlan:
        """
        Graceful degradation as budget pressure rises (∈ [0, 1]).
        Elders drop to the standard peer tier first (audits tolerate cheaper
        models better than synthesis does); peer downgrades last.
        """
        if pressure < 0.70:
            return plan
        if pressure >= 0.90:
            if plan.peer_escalated:
                plan.notes.append("Budget pressure ≥ 0.90: peer reverted to standard tier")
                plan.peer = self.standard_peer_model
                plan.peer_escalated = False
            plan.notes.append("Budget pressure ≥ 0.90: elders dropped to peer tier")
            plan.elder_security = self.standard_peer_model
            plan.elder_structural = self.standard_peer_model
        else:  # 0.70 ≤ pressure < 0.90
            if plan.elder_security != self.standard_peer_model:
                plan.notes.append("Budget pressure ≥ 0.70: structural elder dropped to peer tier")
                plan.elder_structural = self.standard_peer_model
        plan.tier = "degraded"
        log.warning("router.degraded", pressure=round(pressure, 3))
        return plan
