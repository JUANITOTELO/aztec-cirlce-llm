"""
Tests for Youth, Peer, and Elder agent ranks.
"""

import json
import pytest
from aztec_circle.agents.base import extract_json_payload
from aztec_circle.agents.elder import ElderAgent
from aztec_circle.agents.peer import PeerAgent
from aztec_circle.agents.youth import YouthAgent
from aztec_circle.domain.models import SeverityLevel, VerdictStatus


def test_extract_json_payload_variations():
    # Direct JSON
    assert extract_json_payload('{"key": "value"}') == {"key": "value"}

    # Markdown fenced
    fenced = "Here is the response:\n```json\n{\"test\": 123}\n```\nThanks!"
    assert extract_json_payload(fenced) == {"test": 123}

    # Text before and after
    chatter = "Sure! {\"status\": \"ok\"} Hope this helps!"
    assert extract_json_payload(chatter) == {"status": "ok"}


@pytest.mark.asyncio
async def test_youth_agent_run(mock_provider):
    raw_youth_json = json.dumps({
        "radical_ideas": ["Zero-copy memory pool"],
        "identified_risks": [
            {
                "category": "performance",
                "description": "Buffer overrun on burst load",
                "severity": "HIGH",
                "suggested_mitigation": "Enforce static ring buffer length",
                "is_showstopper": False,
            }
        ],
        "adversarial_scenarios": ["1M concurrent sockets open"],
        "override_triggered": False,
    })
    mock_provider.default_response = raw_youth_json

    agent = YouthAgent(persona="chaos_brainstormer", provider=mock_provider)
    out = await agent.run("Build high-performance network server")

    assert out.persona == "chaos_brainstormer"
    assert len(out.radical_ideas) == 1
    assert len(out.identified_risks) == 1
    assert out.identified_risks[0].severity == SeverityLevel.HIGH
    assert out.override_triggered is False


@pytest.mark.asyncio
async def test_peer_agent_run(mock_provider, sample_youth_output):
    raw_peer_json = json.dumps({
        "architecture_overview": "Async event loop architecture",
        "implementation_code": {
            "server.py": "import asyncio\nclass Server: pass"
        },
        "mitigations_applied": ["Static ring buffer used"],
        "assumptions_made": ["Linux epoll available"],
    })
    mock_provider.default_response = raw_peer_json

    agent = PeerAgent(provider=mock_provider)
    out = await agent.run(
        goal="Build high-performance network server",
        youth_risks=[sample_youth_output],
        loop_index=0,
    )

    assert "Async event loop" in out.architecture_overview
    assert "server.py" in out.implementation_code
    assert out.loop_index == 0


@pytest.mark.asyncio
async def test_elder_agent_audit_approved(mock_provider, sample_peer_draft):
    raw_elder_json = json.dumps({
        "status": "APPROVED",
        "weighted_score": 9.0,
        "audit_items": [
            {
                "criterion": "Authentication & Authorization",
                "weight": 1.0,
                "score": 9.0,
                "critique": "Solid implementation",
                "passed": True,
            }
        ],
        "critical_flaws": [],
        "thinking_summary": "Clean code with appropriate bounds",
    })
    mock_provider.default_response = raw_elder_json

    agent = ElderAgent(persona="security_governance", provider=mock_provider)
    verdict = await agent.audit(sample_peer_draft, "Build server")

    assert verdict.status == VerdictStatus.APPROVED
    assert verdict.weighted_score == 9.0
    assert len(verdict.critical_flaws) == 0


@pytest.mark.asyncio
async def test_elder_agent_audit_rejected_due_to_flaw(mock_provider, sample_peer_draft):
    raw_elder_json = json.dumps({
        "status": "REJECTED",
        "weighted_score": 6.5,
        "audit_items": [
            {
                "criterion": "Input Sanitization",
                "weight": 1.0,
                "score": 6.5,
                "critique": "No bounds check",
                "passed": False,
            }
        ],
        "critical_flaws": ["Buffer overflow risk in packet parser"],
        "reworking_instructions": "Add max packet size check",
    })
    mock_provider.default_response = raw_elder_json

    agent = ElderAgent(persona="security_governance", provider=mock_provider)
    verdict = await agent.audit(sample_peer_draft, "Build server")

    assert verdict.status == VerdictStatus.REJECTED
    assert len(verdict.critical_flaws) == 1
    assert "Buffer overflow" in verdict.critical_flaws[0]
