"""
Real-time streaming UI visualizers for Aztec TUI using Rich Live displays.
Provides animated spinners, live token meters, generation throughput speeds,
native thinking/reasoning model support, and live code/file previews for single and parallel LLM invocations.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _extract_active_file(stream_text: str) -> Optional[str]:
    """Detect if the streaming JSON is actively writing a specific file."""
    matches = re.findall(r'"([a-zA-Z0-9_\-./\\]+\.(?:tsx|ts|jsx|js|py|php|sql|json|css|html|md))"\s*:\s*"', stream_text)
    if matches:
        return matches[-1]
    return None


@dataclass
class AgentStreamState:
    agent_id: str
    label: str
    icon: str = "⚡"
    accumulated_text: str = ""
    thought_text: str = ""
    token_count: int = 0
    start_time: float = field(default_factory=time.perf_counter)
    end_time: Optional[float] = None
    completed: bool = False
    is_thinking: bool = False
    error: Optional[str] = None
    custom_status: Optional[str] = None

    @property
    def elapsed_seconds(self) -> float:
        if self.end_time:
            return max(0.01, self.end_time - self.start_time)
        return max(0.01, time.perf_counter() - self.start_time)

    @property
    def tokens_per_sec(self) -> int:
        return int(self.token_count / self.elapsed_seconds)


class SingleStreamVisualizer:
    """
    Live streaming visualizer for a single LLM agent invocation (e.g. Peer Drafter,
    Patch Generator, Build Fixer). Native support for thinking/reasoning models (Gemini 3.7 Flash, Claude 3.7, DeepSeek R1).
    """

    def __init__(
        self,
        console: Optional[Console],
        title: str,
        icon: str = "⚙",
        show_preview: bool = True,
        preview_lines: int = 4,
    ):
        self.console = console or Console()
        self.title = title
        self.icon = icon
        self.show_preview = show_preview
        self.preview_lines = preview_lines

        self.state = AgentStreamState(
            agent_id="single",
            label=title,
            icon=icon,
        )
        self._live: Optional[Live] = None
        self._is_active = False

    def __enter__(self) -> "SingleStreamVisualizer":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self) -> None:
        if self._is_active:
            return
        self.state.start_time = time.perf_counter()
        self._is_active = True
        try:
            self._live = Live(
                self._render(),
                console=self.console,
                refresh_per_second=10,
                transient=True,
            )
            self._live.start()
        except Exception:
            self._live = None

    def on_chunk(self, delta: str, is_thought: bool = False) -> None:
        """Callback invoked on every streaming token chunk from LLMProvider."""
        if not delta:
            return

        if is_thought:
            self.state.thought_text += delta
            self.state.is_thinking = True
        else:
            self.state.accumulated_text += delta
            self.state.is_thinking = False

        total_chars = len(self.state.accumulated_text) + len(self.state.thought_text)
        self.state.token_count = max(1, total_chars // 4)

        if self._live and self._is_active:
            try:
                self._live.update(self._render())
            except Exception:
                pass

    def stop(self) -> None:
        if not self._is_active:
            return
        self._is_active = False
        self.state.end_time = time.perf_counter()
        self.state.completed = True
        if self._live:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None

    def _render(self) -> Panel:
        speed_str = f"{self.state.tokens_per_sec} tok/s" if self.state.token_count > 0 else "streaming..."
        tokens_str = f"{self.state.token_count:,} tokens"
        elapsed_str = f"{self.state.elapsed_seconds:.1f}s"

        header_table = Table.grid(expand=True)
        header_table.add_column(justify="left", ratio=1)
        header_table.add_column(justify="right")

        title_text = Text()
        if self.state.is_thinking:
            title_text.append("🧠 ", style="bold yellow")
            title_text.append(f"{self.title} [Thinking & Planning...]", style="bold yellow")
        else:
            title_text.append(f"{self.icon} ", style="bold cyan")
            title_text.append(self.title, style="bold white")

        metric_text = Text()
        metric_text.append(f"⚡ {tokens_str}  │  ", style="bold cyan")
        metric_text.append(f"{speed_str}  │  ", style="dim cyan")
        metric_text.append(f"⏱ {elapsed_str}", style="dim white")

        header_table.add_row(title_text, metric_text)

        elements = [header_table]

        # Check for active file drafting
        active_file = _extract_active_file(self.state.accumulated_text)
        if active_file and not self.state.is_thinking:
            file_badge = Text()
            file_badge.append("  📄 Writing File: ", style="bold green")
            file_badge.append(active_file, style="bold white underline")
            elements.append(file_badge)

        if self.show_preview:
            preview_source = self.state.thought_text if self.state.is_thinking else self.state.accumulated_text
            if preview_source:
                lines = [l for l in preview_source.splitlines() if l.strip()]
                tail = lines[-self.preview_lines:] if len(lines) > self.preview_lines else lines
                if tail:
                    style_str = "dim italic yellow" if self.state.is_thinking else "dim white"
                    border_str = "dim yellow" if self.state.is_thinking else "dim blue"
                    preview_text = Text("\n".join(tail), style=style_str)
                    elements.append(Panel(preview_text, border_style=border_str, box=None, padding=(0, 1)))

        panel_border = "yellow" if self.state.is_thinking else "blue"
        return Panel(
            Group(*elements),
            border_style=panel_border,
            padding=(0, 1),
        )


class ParallelStreamVisualizer:
    """
    Live streaming visualizer for multiple concurrent agents running in parallel
    (e.g. Youth Chaos + Devil's Advocate, Elder Security + Structural Councils).
    """

    def __init__(
        self,
        console: Optional[Console],
        title: str,
        icon: str = "🧠",
        border_style: str = "yellow",
    ):
        self.console = console or Console()
        self.title = title
        self.icon = icon
        self.border_style = border_style
        self.agents: Dict[str, AgentStreamState] = {}
        self._live: Optional[Live] = None
        self._is_active = False

    def register_agent(self, agent_id: str, label: str, icon: str = "•") -> Callable[..., None]:
        """Register an agent in the parallel dashboard and return its on_chunk callback."""
        state = AgentStreamState(agent_id=agent_id, label=label, icon=icon)
        self.agents[agent_id] = state

        def _on_chunk(delta: str, is_thought: bool = False) -> None:
            if not delta:
                return
            if is_thought:
                state.thought_text += delta
                state.is_thinking = True
            else:
                state.accumulated_text += delta
                state.is_thinking = False

            total_chars = len(state.accumulated_text) + len(state.thought_text)
            state.token_count = max(1, total_chars // 4)

            if self._live and self._is_active:
                try:
                    self._live.update(self._render())
                except Exception:
                    pass

        return _on_chunk

    def complete_agent(self, agent_id: str, custom_status: Optional[str] = None) -> None:
        """Mark a specific agent stream as completed."""
        if agent_id in self.agents:
            st = self.agents[agent_id]
            st.end_time = time.perf_counter()
            st.completed = True
            if custom_status:
                st.custom_status = custom_status
            if self._live and self._is_active:
                try:
                    self._live.update(self._render())
                except Exception:
                    pass

    def __enter__(self) -> "ParallelStreamVisualizer":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()

    def start(self) -> None:
        if self._is_active:
            return
        self._is_active = True
        try:
            self._live = Live(
                self._render(),
                console=self.console,
                refresh_per_second=10,
                transient=True,
            )
            self._live.start()
        except Exception:
            self._live = None

    def stop(self) -> None:
        if not self._is_active:
            return
        self._is_active = False
        for st in self.agents.values():
            if not st.completed:
                st.end_time = time.perf_counter()
                st.completed = True
        if self._live:
            try:
                self._live.stop()
            except Exception:
                pass
            self._live = None

    def _render(self) -> Panel:
        table = Table.grid(padding=(0, 2), expand=True)
        table.add_column(style="bold white", width=26)
        table.add_column(style="dim", width=22)
        table.add_column(style="bold cyan", justify="right")

        for agent in self.agents.values():
            name_text = Text()
            name_text.append(f"{agent.icon} ", style="cyan")
            name_text.append(agent.label, style="bold white")

            status_text = Text()
            if agent.completed:
                status_text.append("✓ Completed", style="bold green")
                if agent.custom_status:
                    status_text.append(f" ({agent.custom_status})", style="dim green")
            elif agent.is_thinking:
                status_text.append("🧠 Thinking...", style="bold yellow")
            else:
                status_text.append("⠋ Streaming...", style="bold cyan")

            metric_text = Text()
            tok_str = f"{agent.token_count:,} tok"
            spd_str = f"{agent.tokens_per_sec} tok/s" if agent.token_count > 0 else "streaming..."
            el_str = f"{agent.elapsed_seconds:.1f}s"
            metric_text.append(f"{tok_str} │ {spd_str} │ {el_str}", style="dim cyan")

            table.add_row(name_text, status_text, metric_text)

        return Panel(
            table,
            title=f"[{self.border_style}]{self.icon} {self.title}[/{self.border_style}]",
            border_style=self.border_style,
            padding=(0, 1),
        )
