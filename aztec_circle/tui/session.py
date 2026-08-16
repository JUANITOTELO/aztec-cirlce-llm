"""
Session state for the Aztec interactive TUI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from aztec_circle.domain.models import FallbackPolicy
from aztec_circle.config import settings


@dataclass
class SessionState:
    """Tracks state across the interactive Aztec TUI session."""

    total_cost_usd: float = 0.0
    total_tokens: int = 0
    loop_count: int = 0
    budget_limit_usd: float = 1.00
    max_loops: int = 2
    fallback_policy: FallbackPolicy = FallbackPolicy.HUMAN_IN_THE_LOOP
    active_task_id: Optional[str] = None
    output_dir: str = "./aztec_output"
    primary_model: str = field(default_factory=lambda: settings.PEER_MODEL)
    active_server: Optional[Any] = None
    last_goal: Optional[str] = None
    edit_mode_enabled: bool = True
    attached_images: List[str] = field(default_factory=list)

    def record_run(self, cost_usd: float, tokens: int, loops: int, task_id: str):
        """Accumulate usage from a completed debate run."""
        self.total_cost_usd += cost_usd
        self.total_tokens += tokens
        self.loop_count = loops
        self.active_task_id = task_id

    def prompt_text(self) -> str:
        """Render the dynamic prompt bar with optional vision badge."""
        model_short = self.primary_model.split("/")[-1]
        img_badge = f" | 📷 {len(self.attached_images)}" if self.attached_images else ""
        return f"[aztec ({model_short}){img_badge} | ${self.total_cost_usd:.2f}] ❯ "
