"""
Domain models for the Aztec Decision Circle.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


# --- Enumerations ---

class AgentRank(str, Enum):
    YOUTH = "YOUTH"
    PEER = "PEER"
    ELDER = "ELDER"


class CirclePhase(str, Enum):
    IDLE = "IDLE"
    YOUTH_BRAINSTORM = "YOUTH_BRAINSTORM"          # Parallel: Chaos + Advocate
    YOUTH_OVERRIDE_CHECK = "YOUTH_OVERRIDE_CHECK"  # Anomaly Gate
    PEER_DRAFTING = "PEER_DRAFTING"                # Sequential drafting & MCP tool usage
    ELDER_AUDIT = "ELDER_AUDIT"                    # Parallel: Security + Structural
    ARBITRATION = "ARBITRATION"                    # Consensus calculation
    RESOLVED = "RESOLVED"                          # Approved deliverable ready
    EMERGENCY_HALTED = "EMERGENCY_HALTED"          # Critical anomaly stop
    ESCALATED = "ESCALATED"                        # Loop limit or budget fallback


class VerdictStatus(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    HALT_OVERRIDE = "HALT_OVERRIDE"


class FallbackPolicy(str, Enum):
    """Applied when MAX_DEBATE_LOOPS exhausted without consensus."""
    BEST_EFFORT_RELEASE = "BEST_EFFORT_RELEASE"  # Release best draft with anomaly flags
    HUMAN_IN_THE_LOOP = "HUMAN_IN_THE_LOOP"      # Pause and request operator decision
    ABORT = "ABORT"                              # Hard stop, persist state, raise exception


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# --- Youth Rank Models ---

class YouthRiskItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    category: str
    description: str
    severity: SeverityLevel
    suggested_mitigation: str
    is_showstopper: bool = False


class YouthBrainstormOutput(BaseModel):
    agent_id: str
    persona: str = "chaos_brainstormer"
    radical_ideas: List[str] = Field(default_factory=list)
    identified_risks: List[YouthRiskItem] = Field(default_factory=list)
    adversarial_scenarios: List[str] = Field(default_factory=list)
    override_triggered: bool = False
    override_rationale: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    tokens_used: int = 0


# --- Peer Rank Models ---

class ToolCallResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: str
    duration_ms: float = 0.0
    sandboxed: bool = True


class PeerDraftOutput(BaseModel):
    agent_id: str = "code_drafter"
    loop_index: int = 0
    architecture_overview: str
    implementation_code: Dict[str, str] = Field(default_factory=dict)
    mitigations_applied: List[str] = Field(default_factory=list)
    assumptions_made: List[str] = Field(default_factory=list)
    tool_calls: List[ToolCallResult] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    tokens_used: int = 0


# --- Elder Rank Models ---

class ElderAuditItem(BaseModel):
    criterion: str
    weight: float = Field(..., ge=0.0, le=1.0, description="Weight in consensus sum")
    score: float = Field(..., ge=0.0, le=10.0)
    critique: str
    passed: bool


class ElderVerdict(BaseModel):
    agent_id: str
    persona: str = "security_governance"
    status: VerdictStatus
    weighted_score: float = Field(..., ge=0.0, le=10.0)
    audit_items: List[ElderAuditItem] = Field(default_factory=list)
    critical_flaws: List[str] = Field(default_factory=list)
    reworking_instructions: Optional[str] = None
    thinking_summary: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    tokens_used: int = 0


# --- Session State Model ---

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CircleRunState(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    goal: str
    fallback_policy: FallbackPolicy = FallbackPolicy.HUMAN_IN_THE_LOOP
    current_phase: CirclePhase = CirclePhase.IDLE
    loop_count: int = 0
    max_loops: int = 2
    youth_outputs: List[YouthBrainstormOutput] = Field(default_factory=list)
    peer_history: List[PeerDraftOutput] = Field(default_factory=list)
    elder_verdicts: List[ElderVerdict] = Field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    budget_limit_usd: float = 1.00
    final_output: Optional[Dict[str, Any]] = None
    escalation_message: Optional[str] = None
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
