"""
PlasticityEngine: the neuroplasticity hub of the Aztec Decision Circle.

Coordinates the four plastic mechanisms and persists their adaptive state to a
small JSON file so learning survives across processes:

    {
      "version": 1,
      "synaptic": {"security_governance": 0.61, "structural_perf": 0.39},
      "homeostasis": {"approval_threshold": 8.15, "flaw_recurrence_multiplier": 1.05}
    }

The engine is deliberately synchronous and side-effect-free apart from its own
files, so it is trivially testable and safe to call from async orchestration.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import structlog

from aztec_circle.config import settings
from aztec_circle.domain.models import ElderVerdict
from aztec_circle.plasticity.homeostasis import HomeostaticThresholds
from aztec_circle.plasticity.memory import ExperienceMemory
from aztec_circle.plasticity.router import DynamicModelRouter, RoutingPlan
from aztec_circle.plasticity.synaptic import SynapticWeightAdapter

log = structlog.get_logger(__name__)

_STATE_VERSION = 1


class PlasticityEngine:
    def __init__(
        self,
        state_path: Optional[str] = None,
        memory_db_path: Optional[str] = None,
        enabled: Optional[bool] = None,
    ):
        self.enabled = settings.PLASTICITY_ENABLED if enabled is None else bool(enabled)
        self.state_path = Path(state_path or settings.PLASTICITY_STATE_PATH).expanduser()
        self.memory = ExperienceMemory(memory_db_path or settings.PLASTICITY_DB_PATH)
        self.router = DynamicModelRouter()

        self.synaptic = SynapticWeightAdapter()
        self.homeostasis = HomeostaticThresholds(
            base_threshold=settings.PLASTICITY_BASE_THRESHOLD,
            floor=settings.PLASTICITY_THRESHOLD_FLOOR,
            ceiling=settings.PLASTICITY_THRESHOLD_CEILING,
        )
        self._current_plan: Optional[RoutingPlan] = None
        self._run_started_at: Optional[float] = None

        if self.enabled:
            self._load_state()

    # ── State persistence ────────────────────────────────────────────────
    def _load_state(self) -> None:
        try:
            if not self.state_path.exists():
                return
            data = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.synaptic.load_state(data.get("synaptic") or {})
                self.homeostasis.load_state(data.get("homeostasis") or {})
                log.info("plasticity.state_loaded", path=str(self.state_path))
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("plasticity.state_load_failed", error=str(exc))

    def save_state(self) -> None:
        if not self.enabled:
            return
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "version": _STATE_VERSION,
                "synaptic": self.synaptic.snapshot(),
                "homeostasis": self.homeostasis.snapshot(),
            }
            tmp_path = self.state_path.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            os.replace(tmp_path, self.state_path)
        except OSError as exc:
            log.warning("plasticity.state_save_failed", error=str(exc))

    def reset(self) -> None:
        """Full metaplastic reset: forget all learned state and history."""
        self.synaptic = SynapticWeightAdapter()
        self.homeostasis = HomeostaticThresholds(
            base_threshold=settings.PLASTICITY_BASE_THRESHOLD,
            floor=settings.PLASTICITY_THRESHOLD_FLOOR,
            ceiling=settings.PLASTICITY_THRESHOLD_CEILING,
        )
        self.memory.reset()
        self.save_state()
        log.info("plasticity.reset")

    # ── Run lifecycle hooks ──────────────────────────────────────────────
    def on_run_start(self, goal: str, image_count: int = 0) -> RoutingPlan:
        """Compute the routing plan + institutional memory for a new run."""
        plan = self.router.plan(goal, image_count=image_count)
        pressure = self.budget_pressure()
        if pressure > 0:
            plan = self.router.degrade_for_budget(plan, pressure)
        self._current_plan = plan
        self._run_started_at = time.time()
        return plan

    def institutional_memory(self, max_insights: int = 5) -> Optional[str]:
        return self.memory.insights_for_goal(max_insights=max_insights)

    def budget_pressure(self) -> float:
        """
        Current spend relative to limit ∈ [0, ∞), clamped to [0, 1].
        Read from live settings so mid-run budget updates are honored.
        """
        limit = max(1e-9, float(getattr(settings, "BUDGET_LIMIT_USD", 1.0)))
        spent = float(getattr(settings, "_LIVE_SPEND_USD", 0.0) or 0.0)
        return min(1.0, spent / limit) if spent else 0.0

    def on_loop_rejected(self, loop_index: int, consolidated: ElderVerdict) -> Optional[RoutingPlan]:
        """
        Called after each rejected arbitration. Escalates the peer model under
        stress; returns the updated plan (or None when disabled).
        """
        if not self.enabled or self._current_plan is None:
            return self._current_plan
        if loop_index >= 1:
            reason = f"loop {loop_index} rejected (score {consolidated.weighted_score})"
            self._current_plan = self.router.escalate_peer(self._current_plan, reason)
        return self._current_plan

    def on_run_complete(
        self,
        task_id: str,
        goal: str,
        status: str,
        loops_used: int,
        final_score: float,
        cost_usd: float,
        total_tokens: int,
        verdicts: Optional[List[ElderVerdict]] = None,
        consolidated: Optional[ElderVerdict] = None,
    ) -> Dict[str, Any]:
        """
        Close the plasticity loop for one run: update experience memory,
        synaptic weights, homeostatic thresholds, then persist.
        Returns a summary snapshot of what changed.
        """
        approved = status == "APPROVED"
        tier = self._current_plan.tier if self._current_plan else "standard"

        # 1. Experience memory -------------------------------------------------
        known_hashes = self.memory.known_category_hashes()
        all_flaws: List[str] = list(consolidated.critical_flaws or []) if consolidated else []
        mitigations: List[str] = []
        for v in verdicts or []:
            all_flaws.extend(v.critical_flaws or [])
            if v.reworking_instructions:
                mitigations.append(v.reworking_instructions)
        flaw_pairs = self.memory.record_flaws(task_id, all_flaws, mitigations)
        seen_before = sum(1 for _, chash in flaw_pairs if chash in known_hashes)
        recurrence_ratio = (seen_before / len(flaw_pairs)) if flaw_pairs else 0.0

        self.memory.record_run(
            task_id=task_id,
            goal=goal,
            status=status,
            loops_used=loops_used,
            final_score=final_score,
            cost_usd=cost_usd,
            total_tokens=total_tokens,
            tier=tier,
        )

        # 2. Synaptic reinforcement -------------------------------------------
        signals = self._reliability_signals(verdicts or [], consolidated, approved)
        self.synaptic.reinforce(signals)

        # 3. Homeostasis -------------------------------------------------------
        self.homeostasis.record_flaw_recurrence(recurrence_ratio)
        self.homeostasis.record_run(approved=approved, loops_used=max(0, loops_used - 1), max_loops=2)

        # 4. Persist learned state --------------------------------------------
        self.save_state()

        snapshot = self.snapshot()
        log.info("plasticity.run_complete", task_id=task_id, status=status, **snapshot["homeostasis"])
        return snapshot

    def _reliability_signals(
        self,
        verdicts: List[ElderVerdict],
        consolidated: Optional[ElderVerdict],
        approved: bool,
    ) -> Dict[str, float]:
        """
        Map each elder's verdict to a reliability signal ∈ [0, 1]:

        - Approved outcome: elders who scored high are reinforced.
        - Rejected outcome: elders who flagged flaws are reinforced
          (their vigilance was justified); elders who scored high while flaws
          existed are depressed (they missed it).
        """
        signals: Dict[str, float] = {}
        final_score = consolidated.weighted_score if consolidated else 0.0
        flaw_count = len(consolidated.critical_flaws or []) if consolidated else 0

        for v in verdicts:
            key = v.persona.lower().replace("elder_", "")
            if approved:
                signal = max(0.0, min(1.0, v.weighted_score / 10.0))
            else:
                flagged = bool(v.critical_flaws)
                base = 0.85 if flagged else (max(0.0, 0.6 - flaw_count * 0.1))
                # Elders whose score agreed with the final low score get a boost.
                agreement = 1.0 - abs(v.weighted_score - final_score) / 10.0
                signal = max(0.0, min(1.0, 0.5 * base + 0.5 * agreement))
            signals[key] = signal
        return signals

    # ── Consensus bridge ─────────────────────────────────────────────────
    def consensus_params(self) -> Dict[str, float]:
        """Live parameters to hand to ConsensusEngine."""
        return self.homeostasis.consensus_params()

    def elder_weights(self) -> Dict[str, float]:
        return self.synaptic.consensus_weights()

    # ── Introspection ────────────────────────────────────────────────────
    def snapshot(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "synaptic_weights": self.synaptic.snapshot(),
            "homeostasis": self.homeostasis.snapshot(),
            "routing": self._current_plan.snapshot() if self._current_plan else None,
            "memory_stats": self.memory.stats(),
            "state_path": str(self.state_path),
        }
