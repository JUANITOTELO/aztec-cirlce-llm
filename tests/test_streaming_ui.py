"""
Unit tests for Rich Live streaming visualizers (SingleStreamVisualizer & ParallelStreamVisualizer).
"""

import time
import pytest
from rich.console import Console

from aztec_circle.tui.streaming_ui import (
    SingleStreamVisualizer,
    ParallelStreamVisualizer,
    _extract_active_file,
)


def test_extract_active_file():
    sample_json = '''
    {
      "architecture_overview": "test overview",
      "new_files": {
        "src/components/Products/ProductManager.tsx": "export const ProductManager = () => null;",
        "src/hooks/useProducts.ts": "
    '''
    detected = _extract_active_file(sample_json)
    assert detected == "src/hooks/useProducts.ts"


def test_single_stream_visualizer_lifecycle():
    console = Console(record=True)
    vis = SingleStreamVisualizer(
        console=console,
        title="Peer Drafter Testing",
        icon="⚙",
        show_preview=True,
    )

    with vis:
        vis.on_chunk("export const App = ")
        vis.on_chunk("() => <div>Hello World</div>;\n")
        assert vis.state.token_count > 0
        assert "Hello World" in vis.state.accumulated_text

    assert vis.state.completed is True
    assert vis.state.elapsed_seconds >= 0.0


def test_parallel_stream_visualizer_lifecycle():
    console = Console(record=True)
    p_vis = ParallelStreamVisualizer(
        console=console,
        title="Youth Parallel Brainstorming",
        icon="🧠",
        border_style="yellow",
    )

    on_chunk_1 = p_vis.register_agent("chaos", "Chaos Brainstormer", icon="🌀")
    on_chunk_2 = p_vis.register_agent("advocate", "Devil's Advocate", icon="🛡")

    with p_vis:
        on_chunk_1("Found risk 1: schema conflict\n")
        on_chunk_2("Found risk 2: state collision\n")

        assert p_vis.agents["chaos"].token_count > 0
        assert p_vis.agents["advocate"].token_count > 0

        p_vis.complete_agent("chaos", custom_status="3 risks found")
        assert p_vis.agents["chaos"].completed is True
        assert p_vis.agents["chaos"].custom_status == "3 risks found"

    assert p_vis.agents["advocate"].completed is True
