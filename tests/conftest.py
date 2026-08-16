"""
Pytest configuration, fixtures, and mocks for Aztec Decision Circle tests.
"""

from __future__ import annotations

import json
import os
import tempfile
from typing import Any, Dict, List
import pytest

from aztec_circle.adapters.llm_provider import LLMProvider, LLMResponse
from aztec_circle.domain.models import (
    CircleRunState,
    ElderAuditItem,
    ElderVerdict,
    PeerDraftOutput,
    SeverityLevel,
    VerdictStatus,
    YouthBrainstormOutput,
    YouthRiskItem,
)


class MockLLMProvider(LLMProvider):
    def __init__(self, canned_responses: Dict[str, str] = None, default_response: str = "{}"):
        super().__init__(primary_model="mock-model", fallback_model="mock-fallback")
        self.canned_responses = canned_responses or {}
        self.default_response = default_response
        self.calls: List[Dict[str, Any]] = []

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        temperature: float = 0.7,
        thinking_budget: int = None,
        **kwargs: Any,
    ) -> LLMResponse:
        self.calls.append({
            "messages": messages,
            "model": model or self.primary_model,
            "temperature": temperature,
            "thinking_budget": thinking_budget,
            "kwargs": kwargs,
        })
        # Check system or user prompt matching
        system_content = next((m["content"] for m in messages if m.get("role") == "system"), "")
        content = self.default_response

        for key, canned in self.canned_responses.items():
            if key in system_content or any(key in m.get("content", "") for m in messages):
                content = canned
                break

        return LLMResponse(
            content=content,
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            model=model or self.primary_model,
        )


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def mock_provider():
    return MockLLMProvider()


@pytest.fixture
def sample_youth_output():
    return YouthBrainstormOutput(
        agent_id="youth_chaos_brainstormer",
        persona="chaos_brainstormer",
        radical_ideas=["Use event sourcing", "Zero-copy ring buffer"],
        identified_risks=[
            YouthRiskItem(
                category="concurrency",
                description="Race condition on token refill",
                severity=SeverityLevel.HIGH,
                suggested_mitigation="Use atomic CAS operations",
                is_showstopper=False,
            )
        ],
        adversarial_scenarios=["Burst of 10k requests at millisecond 0"],
        override_triggered=False,
        tokens_used=120,
    )


@pytest.fixture
def sample_peer_draft():
    return PeerDraftOutput(
        agent_id="peer_code_drafter",
        loop_index=0,
        architecture_overview="Token bucket with atomic integer CAS counter.",
        implementation_code={"rate_limiter.py": "class TokenBucket: pass"},
        mitigations_applied=["Atomic operations on refill"],
        assumptions_made=["Single process execution"],
        tokens_used=250,
    )


@pytest.fixture
def sample_elder_verdict_approved():
    return ElderVerdict(
        agent_id="elder_security_governance",
        persona="security_governance",
        status=VerdictStatus.APPROVED,
        weighted_score=9.2,
        audit_items=[
            ElderAuditItem(
                criterion="Authentication & Sanitization",
                weight=1.0,
                score=9.2,
                critique="Exemplary memory bounds and thread safety",
                passed=True,
            )
        ],
        critical_flaws=[],
        tokens_used=180,
    )


@pytest.fixture
def sample_elder_verdict_rejected():
    return ElderVerdict(
        agent_id="elder_security_governance",
        persona="security_governance",
        status=VerdictStatus.REJECTED,
        weighted_score=6.0,
        audit_items=[
            ElderAuditItem(
                criterion="Resource Quotas",
                weight=1.0,
                score=6.0,
                critique="No bounds on bucket queue size",
                passed=False,
            )
        ],
        critical_flaws=["Unbounded queue allows denial of service"],
        reworking_instructions="Cap bucket queue size to max 10,000 items.",
        tokens_used=180,
    )
