"""
Homeostatic threshold adaptation.

The approval threshold and flaw penalty are not constants: they drift toward
the observed quality/efficiency equilibrium of this installation. Runs that
consistently approve on the first loop relax the gate slightly (saving loops
and tokens); runs that exhaust their loop budget tighten it (demanding more
from drafting). Everything is clamped to a safe band so the controller can
never wander into permissiveness or paralysis.
"""

from __future__ import annotations

from typing import Dict, Optional
import structlog

log = structlog.get_logger(__name__)


class HomeostaticThresholds:
    def __init__(
        self,
        base_threshold: float = 8.0,
        floor: float = 7.0,
        ceiling: float = 9.0,
        step: float = 0.15,
        base_flaw_penalty_pct: float = 0.15,
        max_flaw_penalty_pct: float = 0.60,
    ):
        self.base_threshold = base_threshold
        self.floor = floor
        self.ceiling = ceiling
        self.step = step
        self.base_flaw_penalty_pct = base_flaw_penalty_pct
        self.max_flaw_penalty_pct = max_flaw_penalty_pct

        self.approval_threshold: float = base_threshold
        # Recurrence multiplier for flaw penalty ∈ [1.0, 1.5]: repeated flaw
        # categories indicate the drafter ignores them, so punish harder.
        self.flaw_recurrence_multiplier: float = 1.0

    @property
    def flaw_penalty_pct(self) -> float:
        return min(
            self.base_flaw_penalty_pct * self.flaw_recurrence_multiplier,
            self.max_flaw_penalty_pct,
        )

    def _clamp(self) -> None:
        self.approval_threshold = max(self.floor, min(self.ceiling, self.approval_threshold))
        self.flaw_recurrence_multiplier = max(1.0, min(1.5, self.flaw_recurrence_multiplier))

    def record_run(self, approved: bool, loops_used: int, max_loops: int) -> Dict[str, float]:
        """
        Update thresholds from one completed run.

        - Approved on first loop  -> relax (efficiency pressure).
        - Approved on later loops -> hold (equilibrium reached).
        - Escalated / exhausted   -> tighten (quality pressure).
        """
        if approved and loops_used <= 0:
            delta = -self.step
        elif approved:
            delta = 0.0
        else:
            delta = self.step * max(1, min(3, loops_used + 1))

        self.approval_threshold += delta
        self._clamp()
        log.debug(
            "homeostasis.updated",
            approval_threshold=round(self.approval_threshold, 3),
            delta=delta,
            flaw_multiplier=round(self.flaw_recurrence_multiplier, 3),
        )
        return self.snapshot()

    def record_flaw_recurrence(self, recurrence_ratio: float) -> None:
        """
        Adjust flaw-penalty severity from the fraction of flaws in this run
        that were seen before (recurrence_ratio ∈ [0, 1]).
        """
        ratio = max(0.0, min(1.0, recurrence_ratio))
        if ratio >= 0.5:
            self.flaw_recurrence_multiplier += 0.05
        elif ratio <= 0.1:
            self.flaw_recurrence_multiplier = max(1.0, self.flaw_recurrence_multiplier - 0.02)
        self._clamp()

    def consensus_params(self) -> Dict[str, float]:
        return {
            "approval_threshold": round(self.approval_threshold, 4),
            "flaw_penalty_pct": round(self.flaw_penalty_pct, 4),
        }

    def snapshot(self) -> Dict[str, float]:
        return {
            "approval_threshold": round(self.approval_threshold, 4),
            "flaw_recurrence_multiplier": round(self.flaw_recurrence_multiplier, 4),
        }

    def load_state(self, state: Optional[Dict[str, float]]) -> None:
        if not state:
            return
        try:
            self.approval_threshold = float(state.get("approval_threshold", self.approval_threshold))
            self.flaw_recurrence_multiplier = float(
                state.get("flaw_recurrence_multiplier", self.flaw_recurrence_multiplier)
            )
        except (TypeError, ValueError):
            pass
        self._clamp()
