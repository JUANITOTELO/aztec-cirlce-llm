"""
Synaptic weight adaptation for Elder council auditors.

Implements a bounded, decay-regularized Hebbian update: auditors whose
verdicts historically track the consolidated outcome gain influence; auditors
whose verdicts diverge from it lose influence. Weights are normalized and
clamped every step, and an elastic pull toward the baseline prevents
irreversible lock-in (metaplasticity).
"""

from __future__ import annotations

from typing import Dict, List, Optional
import structlog

log = structlog.get_logger(__name__)

DEFAULT_WEIGHTS: Dict[str, float] = {
    "elder_security_governance": 0.60,
    "elder_structural_perf": 0.40,
    "security_governance": 0.60,
    "structural_perf": 0.40,
}


def _canon(name: str) -> str:
    """Canonicalize agent_id/persona to its bare persona key."""
    n = (name or "").strip().lower()
    if n.startswith("elder_"):
        n = n[len("elder_"):]
    return n


class SynapticWeightAdapter:
    """
    Adapts per-auditor consensus weights from outcome feedback.

    reliability_signal ∈ [0, 1]: how well the auditor's verdict agreed with the
    final consolidated outcome (1.0 = perfectly aligned, 0.0 = opposed).
    """

    def __init__(
        self,
        baseline: Optional[Dict[str, float]] = None,
        learning_rate: float = 0.08,
        decay: float = 0.02,
        min_weight: float = 0.15,
        max_weight: float = 0.80,
        persona_keys: Optional[List[str]] = None,
    ):
        self.baseline = {k: v for k, v in (baseline or DEFAULT_WEIGHTS).items()}
        self.learning_rate = learning_rate
        self.decay = decay
        self.min_weight = min_weight
        self.max_weight = max_weight
        # Live synaptic state, keyed by canonical persona.
        self.persona_keys = persona_keys or ["security_governance", "structural_perf"]
        self.state: Dict[str, float] = {}
        for key in self.persona_keys:
            ck = _canon(key)
            base_vals = [v for k, v in self.baseline.items() if _canon(k) == ck]
            self.state[ck] = base_vals[0] if base_vals else 1.0 / max(1, len(self.persona_keys))
        self._normalize()

    def _normalize(self) -> None:
        """
        Project weights onto the simplex intersected with [min,max] bounds.
        Iterative water-filling: each pass moves unclamped mass toward the
        deficit until the sum is exactly 1.0 (or bounds make it impossible).
        """
        keys = list(self.state.keys())
        total = sum(self.state.values()) or 1.0
        w = {k: v / total for k, v in self.state.items()}

        for _ in range(100):
            deficit = 1.0 - sum(w.values())
            if abs(deficit) < 1e-9:
                break
            # Room to grow (deficit>0) or shrink (deficit<0) without violating bounds.
            if deficit > 0:
                room = {
                    k: self.max_weight - w[k]
                    for k in keys
                    if w[k] < self.max_weight - 1e-12
                }
            else:
                room = {
                    k: w[k] - self.min_weight
                    for k in keys
                    if w[k] > self.min_weight + 1e-12
                }
            total_room = sum(max(0.0, r) for r in room.values())
            if total_room <= 1e-12:
                break  # bounds infeasible; accept best-effort state
            for k, room_k in room.items():
                w[k] += deficit * (room_k / total_room)
            for k in keys:
                w[k] = max(self.min_weight, min(self.max_weight, w[k]))

        self.state = {k: round(v, 6) for k, v in w.items()}

    def reinforce(self, signals: Dict[str, float]) -> Dict[str, float]:
        """
        Apply one plasticity step.

        signals maps canonical persona -> reliability ∈ [0, 1]. Personas not
        present in `signals` receive pure elastic decay toward baseline.
        Returns the updated state.
        """
        lr = max(0.0, min(1.0, self.learning_rate))
        for key in list(self.state.keys()):
            target_baseline = 0.0
            base_matches = [v for k, v in self.baseline.items() if _canon(k) == key]
            if base_matches:
                # Normalize this persona's baseline share against current keys.
                base_sum = sum(
                    bv
                    for bk, bv in self.baseline.items()
                    if _canon(bk) in self.state
                ) or 1.0
                target_baseline = base_matches[0] / base_sum

            signal = signals.get(key)
            if signal is not None:
                signal = max(0.0, min(1.0, signal))
                # Soft-Hebbian potentiation/depression toward observed reliability.
                self.state[key] += lr * (signal * 2.0 - 1.0) * self.state[key]
            # Elastic decay toward baseline (never fully forget).
            self.state[key] += self.decay * (target_baseline - self.state[key])

        self._normalize()
        log.debug("synaptic.updated", state=self.state)
        return dict(self.state)

    def consensus_weights(self) -> Dict[str, float]:
        """
        Export weights keyed for ConsensusEngine lookup: both bare-persona and
        'elder_'-prefixed forms so agent_id or persona both resolve.
        """
        out: Dict[str, float] = {}
        for key, value in self.state.items():
            out[key] = value
            out[f"elder_{key}"] = value
        return out

    def snapshot(self) -> Dict[str, float]:
        return dict(self.state)

    def load_state(self, state: Dict[str, float]) -> None:
        for key, value in (state or {}).items():
            ck = _canon(key)
            if ck in self.state:
                try:
                    self.state[ck] = float(value)
                except (TypeError, ValueError):
                    continue
        self._normalize()
