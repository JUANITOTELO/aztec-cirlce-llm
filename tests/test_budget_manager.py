"""
Tests for budget manager and circuit breaker threshold enforcement.
"""

import pytest
from aztec_circle.domain.exceptions import BudgetExceeded
from aztec_circle.engine.budget_manager import BudgetManager


def test_budget_recording_and_cost():
    bm = BudgetManager(limit_usd=1.00, input_cost_per_m=3.00, output_cost_per_m=15.00)
    # 100k input = $0.30, 20k output = $0.30 -> total $0.60
    cost = bm.record(input_tokens=100_000, output_tokens=20_000)
    assert round(cost, 4) == 0.6000
    assert bm.total_tokens == 120_000
    # No exception when checked
    bm.check()


def test_budget_exceeded_raises_exception():
    bm = BudgetManager(limit_usd=0.50, input_cost_per_m=3.00, output_cost_per_m=15.00)
    # 200k input = $0.60 (> 0.50)
    bm.record(input_tokens=200_000, output_tokens=0)
    with pytest.raises(BudgetExceeded) as exc_info:
        bm.check()
    assert "Budget limit of $0.5000 exceeded" in str(exc_info.value)
