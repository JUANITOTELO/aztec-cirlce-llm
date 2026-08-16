"""
Budget circuit breaker and token expenditure manager.
"""

from __future__ import annotations

from typing import Tuple
import structlog

from aztec_circle.config import settings
from aztec_circle.domain.exceptions import BudgetExceeded

log = structlog.get_logger(__name__)

# Default price estimations per 1 Million tokens
DEFAULT_INPUT_COST_PER_M = 3.00   # $3.00 / 1M prompt tokens
DEFAULT_OUTPUT_COST_PER_M = 15.00  # $15.00 / 1M completion tokens


class BudgetManager:
    def __init__(
        self,
        limit_usd: float = 1.00,
        input_cost_per_m: float = DEFAULT_INPUT_COST_PER_M,
        output_cost_per_m: float = DEFAULT_OUTPUT_COST_PER_M,
    ):
        self.limit_usd = limit_usd
        self.input_cost_per_m = input_cost_per_m
        self.output_cost_per_m = output_cost_per_m
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_tokens: int = 0
        self.total_cost_usd: float = 0.0

    def record(self, input_tokens: int = 0, output_tokens: int = 0, total_tokens: int = 0) -> float:
        """
        Record token usage, compute incremental cost, and return total cost.
        """
        if total_tokens > 0 and input_tokens == 0 and output_tokens == 0:
            # Approximate split: 70% input, 30% output
            input_tokens = int(total_tokens * 0.7)
            output_tokens = total_tokens - input_tokens

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_tokens += (input_tokens + output_tokens)

        cost_increment = (
            (input_tokens / 1_000_000.0) * self.input_cost_per_m
            + (output_tokens / 1_000_000.0) * self.output_cost_per_m
        )
        self.total_cost_usd += cost_increment

        log.debug(
            "budget.recorded",
            added_tokens=input_tokens + output_tokens,
            total_tokens=self.total_tokens,
            total_cost_usd=round(self.total_cost_usd, 6),
            limit_usd=self.limit_usd,
        )

        return self.total_cost_usd

    def check(self) -> None:
        """
        Verify that total spend is within the budget limit; raises BudgetExceeded if exceeded.
        """
        if self.total_cost_usd > self.limit_usd:
            raise BudgetExceeded(
                f"Budget limit of ${self.limit_usd:.4f} exceeded! Current spend: ${self.total_cost_usd:.4f}"
            )
