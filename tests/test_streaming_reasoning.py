"""
Unit tests for Gemini 3.7 Flash & reasoning/thought chunk streaming in LLMProvider and TUI visualizers.
"""

import asyncio
import pytest
from unittest.mock import MagicMock
from rich.console import Console

from aztec_circle.adapters.llm_provider import LLMProvider
from aztec_circle.tui.streaming_ui import SingleStreamVisualizer, ParallelStreamVisualizer


class MockDeltaChoice:
    def __init__(self, content="", reasoning_content=""):
        self.delta = MagicMock()
        self.delta.content = content
        self.delta.reasoning_content = reasoning_content
        self.delta.thought = ""
        self.delta.reasoning = ""
        self.delta.thinking = ""


class MockStreamingChunk:
    def __init__(self, content="", reasoning_content="", usage=None):
        self.choices = [MockDeltaChoice(content=content, reasoning_content=reasoning_content)]
        self.usage = usage


class MockAsyncStream:
    def __init__(self, chunks):
        self.chunks = list(chunks)
        self.idx = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.idx >= len(self.chunks):
            raise StopAsyncIteration
        c = self.chunks[self.idx]
        self.idx += 1
        return c


@pytest.mark.asyncio
async def test_stream_response_with_gemini_reasoning_chunks():
    provider = LLMProvider()

    # Simulate Gemini 3.7 Flash: 3 thinking chunks followed by 2 content chunks
    mock_chunks = [
        MockStreamingChunk(reasoning_content="Let's analyze the requirements.\n"),
        MockStreamingChunk(reasoning_content="We should create a product manager component.\n"),
        MockStreamingChunk(reasoning_content="Generating JSON response now.\n"),
        MockStreamingChunk(content='{"architecture_overview": "Product management", '),
        MockStreamingChunk(content='"new_files": {}}'),
    ]

    received_chunks = []
    thought_chunks = []

    def on_chunk_cb(text, is_thought=False):
        if is_thought:
            thought_chunks.append(text)
        else:
            received_chunks.append(text)

    stream_iter = MockAsyncStream(mock_chunks)
    full_content, usage, last_chunk = await provider._stream_response(stream_iter, on_chunk=on_chunk_cb)

    # Clean JSON payload returned without raw thoughts prepended
    assert full_content == '{"architecture_overview": "Product management", "new_files": {}}'

    # All thought tokens were delivered to the UI callback
    assert len(thought_chunks) == 3
    assert "Let's analyze" in thought_chunks[0]

    # All content tokens were delivered to the UI callback
    assert len(received_chunks) == 2
    assert "Product management" in received_chunks[0]


def test_single_stream_visualizer_thinking_transition():
    console = Console(record=True)
    vis = SingleStreamVisualizer(
        console=console,
        title="Peer Drafter with Thinking",
        icon="⚙",
        show_preview=True,
    )

    with vis:
        # 1. Thinking phase
        vis.on_chunk("Thinking about product database architecture...\n", is_thought=True)
        assert vis.state.is_thinking is True
        assert vis.state.token_count > 0
        assert "Thinking about product" in vis.state.thought_text

        # 2. Content generation phase
        vis.on_chunk('{"new_files": {"src/components/Products/ProductManager.tsx": "export const ProductManager = () => null;"}}', is_thought=False)
        assert vis.state.is_thinking is False
        assert "src/components/Products/ProductManager.tsx" in vis.state.accumulated_text


def test_parallel_stream_visualizer_thinking_transition():
    console = Console(record=True)
    p_vis = ParallelStreamVisualizer(
        console=console,
        title="Youth Brainstorming Thinking",
        icon="🧠",
    )

    on_chunk_chaos = p_vis.register_agent("chaos", "Chaos Brainstormer", icon="🌀")
    on_chunk_advocate = p_vis.register_agent("advocate", "Devil's Advocate", icon="🛡")

    with p_vis:
        # Chaos is thinking
        on_chunk_chaos("Analyzing state collisions in store.ts...\n", is_thought=True)
        assert p_vis.agents["chaos"].is_thinking is True
        assert p_vis.agents["chaos"].token_count > 0

        # Advocate outputs content directly
        on_chunk_advocate("Risk: Migration lock contention\n", is_thought=False)
        assert p_vis.agents["advocate"].is_thinking is False
        assert p_vis.agents["advocate"].token_count > 0

        # Chaos switches to content
        on_chunk_chaos('{"identified_risks": []}', is_thought=False)
        assert p_vis.agents["chaos"].is_thinking is False
