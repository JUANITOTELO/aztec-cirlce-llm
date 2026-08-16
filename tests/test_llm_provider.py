"""
Tests for LLM resilience adapter, retries, and fallback failover.
"""

from unittest.mock import AsyncMock, patch
import litellm
import pytest
from aztec_circle.adapters.llm_provider import LLMProvider, LLMResponse
from aztec_circle.domain.exceptions import LLMProviderFailure


@pytest.mark.asyncio
async def test_llm_provider_success():
    provider = LLMProvider(primary_model="mock-gpt")

    mock_litellm_resp = AsyncMock()
    mock_litellm_resp.choices = [
        AsyncMock(message=AsyncMock(content='{"status": "ok"}'))
    ]
    mock_litellm_resp.usage = AsyncMock(prompt_tokens=50, completion_tokens=25, total_tokens=75)

    with patch("litellm.acompletion", return_value=mock_litellm_resp):
        resp = await provider.complete(
            messages=[{"role": "user", "content": "hello"}],
            model="mock-gpt",
        )
        assert resp.content == '{"status": "ok"}'
        assert resp.prompt_tokens == 50
        assert resp.completion_tokens == 25
        assert resp.total_tokens == 75


@pytest.mark.asyncio
async def test_llm_provider_failover_to_fallback():
    provider = LLMProvider(primary_model="primary-failing", fallback_model="fallback-working")

    fallback_resp = AsyncMock()
    fallback_resp.choices = [
        AsyncMock(message=AsyncMock(content="fallback output"))
    ]
    fallback_resp.usage = AsyncMock(prompt_tokens=30, completion_tokens=10, total_tokens=40)

    async def side_effect(model, **kwargs):
        if model == "primary-failing":
            raise litellm.APIError(status_code=500, message="Provider Down", llm_provider="test")
        return fallback_resp

    with patch("litellm.acompletion", side_effect=side_effect):
        resp = await provider.complete(
            messages=[{"role": "user", "content": "ping"}],
            model="primary-failing",
        )
        assert resp.content == "fallback output"
        assert resp.model == "fallback-working"


@pytest.mark.asyncio
async def test_llm_provider_both_fail():
    provider = LLMProvider(primary_model="primary-failing", fallback_model="fallback-failing")

    with patch("litellm.acompletion", side_effect=Exception("Unrecoverable error")):
        with pytest.raises(LLMProviderFailure):
            await provider.complete(
                messages=[{"role": "user", "content": "ping"}],
                model="primary-failing",
            )
