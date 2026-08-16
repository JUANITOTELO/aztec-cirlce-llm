"""
Aztec Decision Circle state machine and orchestrator engine.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
import structlog

from aztec_circle.agents.elder import ElderAgent
from aztec_circle.agents.peer import PeerAgent
from aztec_circle.agents.youth import YouthAgent
from aztec_circle.config import settings
from aztec_circle.domain.exceptions import (
    BudgetExceeded,
    LoopLimitExceeded,
    YouthOverrideHalt,
)
from aztec_circle.domain.models import (
    CirclePhase,
    CircleRunState,
    FallbackPolicy,
    VerdictStatus,
    YouthBrainstormOutput,
)
from aztec_circle.engine.budget_manager import BudgetManager
from aztec_circle.engine.checkpoint import CheckpointStore
from aztec_circle.engine.consensus import ConsensusEngine

log = structlog.get_logger(__name__)


class AztecOrchestrator:
    def __init__(
        self,
        state: CircleRunState,
        event_queue: Optional[asyncio.Queue] = None,
        checkpoint_store: Optional[CheckpointStore] = None,
        budget_manager: Optional[BudgetManager] = None,
        consensus_engine: Optional[ConsensusEngine] = None,
        youth_agents: Optional[List[YouthAgent]] = None,
        peer_agent: Optional[PeerAgent] = None,
        elder_agents: Optional[List[ElderAgent]] = None,
    ):
        self.state = state
        self.events = event_queue or asyncio.Queue()
        self.checkpoint = checkpoint_store or CheckpointStore()
        self.budget = budget_manager or BudgetManager(limit_usd=state.budget_limit_usd)
        self.consensus = consensus_engine or ConsensusEngine()

        self.youth_agents = youth_agents or [
            YouthAgent(persona="chaos_brainstormer"),
            YouthAgent(persona="devils_advocate"),
        ]
        self.peer_agent = peer_agent or PeerAgent()
        self.elder_agents = elder_agents or [
            ElderAgent(persona="security_governance"),
            ElderAgent(persona="structural_perf"),
        ]

    async def run(self) -> Dict[str, Any]:
        """
        Execute the full multi-generational debate cycle.
        """
        log.info("orchestrator.run_started", task_id=self.state.task_id, goal=self.state.goal[:80])

        # ── PHASE 1: Youth Brainstorming (Parallel Execution) ────────────────
        if not self.state.youth_outputs:
            await self._transition(CirclePhase.YOUTH_BRAINSTORM)
            youth_tasks = [agent.run(self.state.goal, images=self.state.images) for agent in self.youth_agents]
            youth_results = await asyncio.gather(*youth_tasks, return_exceptions=True)

            for res in youth_results:
                if isinstance(res, Exception):
                    log.error("orchestrator.youth_agent_error", error=str(res))
                    await self._emit("youth.error", {"error": str(res)})
                    continue
                self.state.youth_outputs.append(res)
                self._record_tokens(res.input_tokens, res.output_tokens, res.tokens_used)

            await self.checkpoint.save(self.state)

        # ── PHASE 2: Youth Override Gate ──────────────────────────────────────
        await self._transition(CirclePhase.YOUTH_OVERRIDE_CHECK)
        all_risks = [r for yo in self.state.youth_outputs for r in yo.identified_risks]
        showstoppers = [r for r in all_risks if r.is_showstopper]
        overrides = [yo for yo in self.state.youth_outputs if yo.override_triggered]

        if showstoppers or overrides:
            rationale_parts = []
            for r in showstoppers:
                rationale_parts.append(f"[{r.severity.value}] {r.description}")
            for yo in overrides:
                if yo.override_rationale:
                    rationale_parts.append(f"Override: {yo.override_rationale}")

            full_rationale = "; ".join(rationale_parts) or "Critical anomaly detected in task goal."
            self.state.current_phase = CirclePhase.EMERGENCY_HALTED
            self.state.escalation_message = f"HALT: {full_rationale}"
            self.state.final_output = {
                "status": "EMERGENCY_HALTED",
                "rationale": full_rationale,
                "risks": [r.model_dump() for r in showstoppers],
            }
            await self.checkpoint.save(self.state)
            await self._emit("override.halt", {"rationale": full_rationale})
            raise YouthOverrideHalt(full_rationale)

        # ── PHASE 3 & 4: Peer Drafting & Elder Auditing Loops ──────────────────
        elder_instructions: Optional[str] = None
        best_draft = None
        last_verdict = None

        while self.state.loop_count <= self.state.max_loops:
            # Phase 3: Peer Drafting
            await self._transition(CirclePhase.PEER_DRAFTING)
            self.budget.check()

            draft = await self.peer_agent.run(
                goal=self.state.goal,
                youth_risks=self.state.youth_outputs,
                elder_instructions=elder_instructions,
                loop_index=self.state.loop_count,
                images=self.state.images,
            )
            self.state.peer_history.append(draft)
            best_draft = draft
            self._record_tokens(draft.input_tokens, draft.output_tokens, draft.tokens_used)
            await self.checkpoint.save(self.state)

            # Phase 4: Elder Auditing (Parallel Execution)
            await self._transition(CirclePhase.ELDER_AUDIT)
            self.budget.check()

            elder_tasks = [agent.audit(draft, self.state.goal, images=self.state.images) for agent in self.elder_agents]
            verdicts = await asyncio.gather(*elder_tasks)

            for v in verdicts:
                self.state.elder_verdicts.append(v)
                self._record_tokens(v.input_tokens, v.output_tokens, v.tokens_used)

            # Phase 5: Arbitration
            await self._transition(CirclePhase.ARBITRATION)
            consolidated_verdict = self.consensus.arbitrate(verdicts)
            last_verdict = consolidated_verdict

            await self._emit(
                "arbitration.result",
                {
                    "loop": self.state.loop_count,
                    "score": consolidated_verdict.weighted_score,
                    "status": consolidated_verdict.status.value,
                    "flaws": consolidated_verdict.critical_flaws,
                },
            )

            if consolidated_verdict.status == VerdictStatus.APPROVED:
                self.state.current_phase = CirclePhase.RESOLVED
                self.state.final_output = {
                    "task_id": self.state.task_id,
                    "goal": self.state.goal,
                    "status": "APPROVED",
                    "loop_count": self.state.loop_count,
                    "total_cost_usd": round(self.state.total_cost_usd, 6),
                    "total_tokens_used": self.state.total_tokens_used,
                    "verdict": consolidated_verdict.model_dump(),
                    "deliverable": draft.model_dump(),
                }
                await self.checkpoint.save(self.state)
                await self._emit("circle.resolved", self.state.final_output)
                return self.state.final_output

            # If rejected, check loop budget
            if self.state.loop_count >= self.state.max_loops:
                log.warning("orchestrator.loops_exhausted", max_loops=self.state.max_loops)
                return await self._handle_fallback(best_draft, last_verdict)

            # Re-arm for next loop iteration
            elder_instructions = consolidated_verdict.reworking_instructions
            self.state.loop_count += 1
            await self.checkpoint.save(self.state)

        return await self._handle_fallback(best_draft, last_verdict)

    async def _handle_fallback(
        self,
        best_draft: Optional[Any],
        last_verdict: Optional[Any],
    ) -> Dict[str, Any]:
        """
        Handle loop exhaustion or budget escalation according to FallbackPolicy.
        """
        await self._transition(CirclePhase.ESCALATED)
        policy = self.state.fallback_policy

        if policy == FallbackPolicy.BEST_EFFORT_RELEASE:
            warning = (
                f"Max loops ({self.state.max_loops}) reached without full consensus. "
                "Delivering best-scored draft with Elder caveat flags."
            )
            self.state.final_output = {
                "task_id": self.state.task_id,
                "status": "ESCALATED_BEST_EFFORT",
                "warning": warning,
                "deliverable": best_draft.model_dump() if best_draft else None,
                "verdict": last_verdict.model_dump() if last_verdict else None,
                "total_cost_usd": round(self.state.total_cost_usd, 6),
            }
        elif policy == FallbackPolicy.HUMAN_IN_THE_LOOP:
            msg = (
                f"Task '{self.state.task_id}' requires human operator review. "
                f"Debate loop exhausted after {self.state.loop_count} iterations. "
                f"Unresolved critical flaws: {last_verdict.critical_flaws if last_verdict else []}"
            )
            self.state.escalation_message = msg
            self.state.final_output = {
                "task_id": self.state.task_id,
                "status": "ESCALATED_HUMAN_IN_THE_LOOP",
                "escalation_message": msg,
                "draft": best_draft.model_dump() if best_draft else None,
                "verdict": last_verdict.model_dump() if last_verdict else None,
                "total_cost_usd": round(self.state.total_cost_usd, 6),
            }
        elif policy == FallbackPolicy.ABORT:
            await self.checkpoint.save(self.state)
            raise LoopLimitExceeded(
                f"Max debate loops ({self.state.max_loops}) exhausted without Elder approval."
            )

        await self.checkpoint.save(self.state)
        await self._emit("circle.escalated", self.state.final_output or {})
        return self.state.final_output or {}

    async def _transition(self, phase: CirclePhase) -> None:
        self.state.current_phase = phase
        await self._emit("phase.change", {
            "task_id": self.state.task_id,
            "phase": phase.value,
            "loop": self.state.loop_count,
            "cost_usd": round(self.state.total_cost_usd, 6),
        })

    async def _emit(self, event: str, payload: Dict[str, Any]) -> None:
        try:
            await self.events.put({"event": event, **payload})
        except Exception as e:
            log.warning("orchestrator.event_emit_failed", error=str(e))

    def _record_tokens(self, input_tokens: int, output_tokens: int, total_tokens: int) -> None:
        self.state.total_input_tokens += input_tokens
        self.state.total_output_tokens += output_tokens
        self.state.total_tokens_used += (input_tokens + output_tokens) if (input_tokens or output_tokens) else total_tokens
        cost = self.budget.record(input_tokens, output_tokens, total_tokens)
        self.state.total_cost_usd = cost
