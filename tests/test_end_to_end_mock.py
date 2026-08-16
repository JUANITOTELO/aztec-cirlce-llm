"""
Full End-to-End Mocked Debate Cycle Test.
Simulates:
- Parallel Youth brainstorming
- Early override clearance
- Loop 0: Peer drafting -> Elder audit rejection with feedback
- Loop 1: Peer revision with Elder feedback -> Elder audit approval
- Consensus arbitration -> RESOLVED state
"""

import asyncio
import json
import pytest
from aztec_circle.agents.elder import ElderAgent
from aztec_circle.agents.peer import PeerAgent
from aztec_circle.agents.youth import YouthAgent
from aztec_circle.domain.models import CirclePhase, CircleRunState, FallbackPolicy
from aztec_circle.engine.checkpoint import CheckpointStore
from aztec_circle.engine.state_machine import AztecOrchestrator
from aztec_circle.adapters.llm_provider import LLMResponse
from tests.conftest import MockLLMProvider


@pytest.mark.asyncio
async def test_full_aztec_debate_loop_with_revision(temp_db_path):
    store = CheckpointStore(db_path=temp_db_path)
    state = CircleRunState(
        goal="Design a fault-tolerant atomic counter in Python",
        max_loops=2,
        budget_limit_usd=1.00,
        fallback_policy=FallbackPolicy.HUMAN_IN_THE_LOOP,
    )
    event_queue: asyncio.Queue = asyncio.Queue()

    # Create dynamic provider that handles iterations
    call_counts = {"elder": 0, "peer": 0}

    class InteractiveMockLLM(MockLLMProvider):
        async def complete(self, messages, model=None, temperature=0.7, thinking_budget=None, **kwargs):
            sys_msg = next((m["content"] for m in messages if m.get("role") == "system"), "")

            # Youth
            if "Youth Rank" in sys_msg or "Chaos" in sys_msg or "Devil" in sys_msg:
                content = json.dumps({
                    "radical_ideas": ["Compare-and-swap with ctypes atomic operations"],
                    "identified_risks": [
                        {
                            "category": "concurrency",
                            "description": "GIL contention on high concurrency",
                            "severity": "HIGH",
                            "suggested_mitigation": "Use lockless CAS loop",
                            "is_showstopper": False,
                        }
                    ],
                    "adversarial_scenarios": ["100 threads incrementing simultaneously"],
                    "override_triggered": False,
                })
            # Peer
            elif "Peer Rank" in sys_msg:
                call_counts["peer"] += 1
                if call_counts["peer"] == 1:
                    # Initial draft (has flaw)
                    content = json.dumps({
                        "architecture_overview": "Thread-safe counter using threading.Lock",
                        "implementation_code": {
                            "counter.py": "import threading\nclass AtomicCounter:\n  def __init__(self):\n    self.val = 0\n  def inc(self):\n    self.val += 1"
                        },
                        "mitigations_applied": ["Initial attempt"],
                        "assumptions_made": ["GIL provides basic protection"],
                    })
                else:
                    # Revised draft (fixed flaw)
                    content = json.dumps({
                        "architecture_overview": "Lockless atomic counter using itertools.count and threading.Lock",
                        "implementation_code": {
                            "counter.py": "import threading\nclass AtomicCounter:\n  def __init__(self):\n    self._val = 0\n    self._lock = threading.Lock()\n  def inc(self):\n    with self._lock:\n      self._val += 1\n      return self._val"
                        },
                        "mitigations_applied": ["Added explicit mutex lock protection"],
                        "assumptions_made": ["CPython runtime"],
                    })
            # Elder
            elif "Elder Rank" in sys_msg or "Auditor" in sys_msg:
                call_counts["elder"] += 1
                # First loop audits (security + structural) -> reject
                if call_counts["elder"] <= 2:
                    content = json.dumps({
                        "status": "REJECTED",
                        "weighted_score": 6.0,
                        "audit_items": [
                            {
                                "criterion": "Concurrency & Race Conditions",
                                "weight": 1.0,
                                "score": 5.0,
                                "critique": "Race condition in self.val += 1 without lock",
                                "passed": False,
                            }
                        ],
                        "critical_flaws": ["Missing thread synchronization in inc()"],
                        "reworking_instructions": "Wrap increment in threading.Lock or use atomic primitive",
                    })
                else:
                    # Second loop audits -> approve
                    content = json.dumps({
                        "status": "APPROVED",
                        "weighted_score": 9.5,
                        "audit_items": [
                            {
                                "criterion": "Concurrency & Race Conditions",
                                "weight": 1.0,
                                "score": 9.5,
                                "critique": "Thread-safe lock applied correctly",
                                "passed": True,
                            }
                        ],
                        "critical_flaws": [],
                        "thinking_summary": "AtomicCounter is now completely thread-safe.",
                    })
            else:
                content = "{}"

            return LLMResponse(
                content=content,
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                model=model or self.primary_model,
            )

    provider = InteractiveMockLLM()
    y1 = YouthAgent(persona="chaos_brainstormer", provider=provider)
    y2 = YouthAgent(persona="devils_advocate", provider=provider)
    peer = PeerAgent(provider=provider)
    e1 = ElderAgent(persona="security_governance", provider=provider)
    e2 = ElderAgent(persona="structural_perf", provider=provider)

    orchestrator = AztecOrchestrator(
        state=state,
        event_queue=event_queue,
        checkpoint_store=store,
        youth_agents=[y1, y2],
        peer_agent=peer,
        elder_agents=[e1, e2],
    )

    result = await orchestrator.run()

    assert result["status"] == "APPROVED"
    assert state.current_phase == CirclePhase.RESOLVED
    assert state.loop_count == 1  # Reached loop 1 and got approved
    assert len(state.peer_history) == 2
    assert len(state.elder_verdicts) >= 3
    assert state.total_cost_usd > 0

    # Verify state in SQLite checkpoint
    persisted = await store.load(state.task_id)
    assert persisted is not None
    assert persisted.current_phase == CirclePhase.RESOLVED
    assert persisted.loop_count == 1
