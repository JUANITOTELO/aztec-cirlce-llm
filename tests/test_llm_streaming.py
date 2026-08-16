"""
Unit tests for Aztec native async streaming, chunk callbacks, and connection resilience.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aztec_circle.adapters.llm_provider import LLMProvider, LLMResponse


class MockAsyncStream:
    """Simulates an async generator for LiteLLM streaming chunks."""
    def __init__(self, chunks, delay: float = 0.0):
        self.chunks = list(chunks)
        self.delay = delay
        self.idx = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        if self.idx >= len(self.chunks):
            raise StopAsyncIteration
        chunk = self.chunks[self.idx]
        self.idx += 1
        return chunk


def make_chunk(text: str, is_final: bool = False, prompt_tokens: int = 0, completion_tokens: int = 0, cached_tokens: int = 0):
    chunk = MagicMock()
    if text:
        choice = MagicMock()
        choice.delta.content = text
        chunk.choices = [choice]
    else:
        chunk.choices = []

    if is_final:
        usage = MagicMock()
        usage.prompt_tokens = prompt_tokens
        usage.completion_tokens = completion_tokens
        usage.total_tokens = prompt_tokens + completion_tokens
        usage.cache_read_input_tokens = cached_tokens
        chunk.usage = usage
    else:
        chunk.usage = None
    return chunk


@pytest.mark.asyncio
async def test_streaming_accumulates_content_and_usage():
    chunks = [
        make_chunk("Hello "),
        make_chunk("from "),
        make_chunk("Aztec!"),
        make_chunk("", is_final=True, prompt_tokens=150, completion_tokens=8, cached_tokens=50),
    ]
    mock_stream = MockAsyncStream(chunks)

    provider = LLMProvider(primary_model="anthropic/claude-sonnet-5", streaming=True)

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acomp:
        mock_acomp.return_value = mock_stream

        resp = await provider.complete([{"role": "user", "content": "Hi"}])
        assert resp.content == "Hello from Aztec!"
        assert resp.prompt_tokens == 150
        assert resp.completion_tokens == 8
        assert resp.total_tokens == 158
        assert resp.cached_tokens == 50
        assert resp.model == "anthropic/claude-sonnet-5"


@pytest.mark.asyncio
async def test_streaming_invokes_on_chunk_callback():
    chunks = [
        make_chunk("Streaming "),
        make_chunk("live "),
        make_chunk("tokens!"),
        make_chunk("", is_final=True, prompt_tokens=100, completion_tokens=10),
    ]
    mock_stream = MockAsyncStream(chunks)

    received_tokens = []
    def chunk_collector(token: str):
        received_tokens.append(token)

    provider = LLMProvider(primary_model="gemini/gemini-3.7-flash", streaming=True)

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acomp:
        mock_acomp.return_value = mock_stream

        resp = await provider.invoke(
            system_prompt="You are an assistant",
            user_message="Hello",
            on_chunk=chunk_collector,
        )
        assert resp.content == "Streaming live tokens!"
        assert received_tokens == ["Streaming ", "live ", "tokens!"]


@pytest.mark.asyncio
async def test_streaming_inactivity_timeout_watchdog():
    # Simulate a stream that stalls longer than chunk_timeout_seconds
    chunks = [
        make_chunk("Starting chunk..."),
        make_chunk("Stalled chunk..."),
    ]
    mock_stream = MockAsyncStream(chunks, delay=0.3)

    provider = LLMProvider(
        primary_model="anthropic/claude-sonnet-5",
        chunk_timeout_seconds=0.1,  # 100ms chunk timeout
        streaming=True,
    )

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acomp:
        mock_acomp.return_value = mock_stream

        with pytest.raises(Exception) as exc_info:
            await provider.complete([{"role": "user", "content": "Hi"}])
        assert "Streaming stalled" in str(exc_info.value) or "failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_streaming_fallback_when_stream_is_regular_object():
    # If litellm returns a regular non-streaming ModelResponse mock
    mock_resp = MagicMock()
    choice = MagicMock()
    choice.message.content = "Non-streamed response"
    mock_resp.choices = [choice]
    mock_resp.usage.prompt_tokens = 50
    mock_resp.usage.completion_tokens = 10
    mock_resp.usage.total_tokens = 60
    mock_resp.usage.cache_read_input_tokens = 0

    provider = LLMProvider(primary_model="openai/gpt-5.6-sol", streaming=True)

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acomp:
        mock_acomp.return_value = mock_resp

        resp = await provider.complete([{"role": "user", "content": "Hi"}])
        assert resp.content == "Non-streamed response"
        assert resp.prompt_tokens == 50
        assert resp.completion_tokens == 10


@pytest.mark.asyncio
async def test_streaming_failover_to_fallback():
    # Primary stream fails, fallback stream succeeds
    fallback_chunks = [
        make_chunk("Fallback "),
        make_chunk("succeeded!"),
        make_chunk("", is_final=True, prompt_tokens=80, completion_tokens=5),
    ]
    fallback_stream = MockAsyncStream(fallback_chunks)

    provider = LLMProvider(
        primary_model="anthropic/claude-sonnet-5",
        fallback_model="gemini/gemini-3.7-flash",
        streaming=True,
    )

    with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acomp:
        mock_acomp.side_effect = [
            RuntimeError("Primary model streaming connection terminated"),
            fallback_stream,
        ]

        resp = await provider.complete([{"role": "user", "content": "Hi"}])
        assert resp.content == "Fallback succeeded!"
        assert resp.model == "gemini/gemini-3.7-flash"
