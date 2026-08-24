"""
Rich terminal renderer, welcome banner, and debate transcript views for Aztec TUI.
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from aztec_circle.config import settings
from aztec_circle.tui.session import SessionState

AZTEC_BANNER = """[bold gold1]
╔════════════════════════════════════════════════════════════════════╗
║  ██████╗ ███████╗████████╗███████╗ ██████╗                         ║
║  ██╔══██╗╚════██║╚══██╔══╝██╔════╝██╔════╝                         ║
║  ███████║    ██╔╝   ██║   █████╗  ██║                              ║
║  ██╔══██║   ██╔╝    ██║   ██╔══╝  ██║                              ║
║  ██║  ██║   ██║     ██║   ███████╗╚██████╗                         ║
║  ╚═╝  ╚═╝   ╚═╝     ╚═╝   ╚══════╝ ╚═════╝                         ║
║         Multi-Generational Adversarial LLM Debate Framework        ║
╚════════════════════════════════════════════════════════════════════╝[/bold gold1]"""

PHASE_FORMATS = {
    "YOUTH_BRAINSTORM": ("🧠 Youth Brainstorm (Parallel Chaos & Devil's Advocate)", "yellow"),
    "YOUTH_OVERRIDE_CHECK": ("✅ Youth Safety & Override Gate", "bright_green"),
    "PEER_DRAFTING": ("⚙  Peer Drafter (Architecture & Code Synthesis)", "blue"),
    "ELDER_AUDIT": ("👁  Elder Council (Security & Structural Audit)", "magenta"),
    "ELDER_COUNCIL": ("👁  Elder Council (Security & Structural Audit)", "magenta"),
    "ARBITRATION": ("⚖  Consensus & Arbitration", "cyan"),
    "CONSENSUS": ("⚖  Consensus & Arbitration", "cyan"),
    "RESOLVED": ("🏁 Resolved Deliverable", "green"),
    "EMERGENCY_HALTED": ("🛑 Emergency Halt Triggered", "bold red"),
    "EMERGENCY_HALT": ("🛑 Emergency Halt Triggered", "bold red"),
    "ESCALATED": ("⚠  Escalated (Loop/Budget Fallback Policy Applied)", "bold yellow"),
    "MODULAR_BRAINSTORM": ("🧩 Modular Brainstorm", "yellow"),
    "MODULAR_DRAFTING": ("🧩 Modular Drafting", "blue"),
    "MODULAR_AUDIT": ("🧩 Modular Audit", "magenta"),
    "MODULAR_RESOLVED": ("🏁 Modular Deliverable Ready", "green"),
}


def _plasticity_banner_row() -> str:
    """Summarize learned neuroplastic state for the welcome banner (safe on failure)."""
    if not settings.PLASTICITY_ENABLED:
        return "[dim]off (PLASTICITY_ENABLED=false)[/dim]"
    try:
        from aztec_circle.plasticity import PlasticityEngine
        engine = PlasticityEngine()
        snap = engine.snapshot()
        threshold = snap["homeostasis"]["approval_threshold"]
        runs = snap["memory_stats"]["total_runs"]
        flaws = snap["memory_stats"]["distinct_flaw_categories"]
        engine.memory.close()
        return (
            f"[bold]on[/bold] · approval gate {threshold} · "
            f"{runs} run(s) learned · {flaws} flaw categories remembered"
        )
    except Exception:
        return "on [dim](state unavailable)[/dim]"


def print_welcome_banner(console: Console, state: SessionState) -> None:
    """Print the launch banner and system overview."""
    import aztec_circle
    console.print(AZTEC_BANNER)

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan", width=16)
    grid.add_column(style="white")

    grid.add_row("Version", f"v{aztec_circle.__version__} [dim](type /update to check latest)[/dim]")
    grid.add_row("Youth Rank", f"{settings.YOUTH_MODEL} [dim](2 parallel agents: chaos & devil's advocate)[/dim]")
    grid.add_row("Peer Rank", f"{settings.PEER_MODEL} [dim](architecture & code synthesis)[/dim]")
    grid.add_row("Elder Rank", f"{settings.ELDER_MODEL} [dim](2 council auditors: security & structural)[/dim]")
    grid.add_row("Neuroplasticity", _plasticity_banner_row())
    grid.add_row("Budget", f"${state.budget_limit_usd:.2f} max per task  |  Fallback: {state.fallback_policy.value}")

    console.print(Panel(grid, title=f"[bold]Active Aztec Engine v{aztec_circle.__version__}[/bold]", border_style="blue", expand=False))
    console.print("[dim]Type your goal to start a debate session, or [bold yellow]/help[/bold yellow] for commands.[/dim]\n")


class TranscriptRenderer:
    """Renders real-time debate progress and finalized deliverables in the terminal."""

    def __init__(self, console: Console):
        self.console = console
        self._current_phase: Optional[str] = None

    def render_phase(self, phase: str) -> None:
        """Render a section divider for a phase transition."""
        if phase != self._current_phase:
            self._current_phase = phase
            title, color = PHASE_FORMATS.get(phase, (f"Phase: {phase}", "white"))
            self.console.print()
            self.console.rule(f"[{color}][bold]{title}[/bold][/{color}]", style=color)

    def render_event(self, event: dict) -> None:
        """Render an event emitted by the Aztec orchestrator (live + legacy formats)."""
        evt_type = event.get("event", "")
        phase = event.get("phase")

        if phase:
            self.render_phase(phase)

        # ── Live orchestrator events ─────────────────────────────────────
        if evt_type == "phase.change":
            # Phase rule already rendered above; show loop/cost context.
            loop = event.get("loop", 0)
            cost = event.get("cost_usd", 0.0) or 0.0
            if loop and loop > 1:
                self.console.print(f"  [dim]↻ revision loop {loop} · spend ${cost:.4f}[/dim]")

        elif evt_type == "arbitration.result":
            approved = str(event.get("status", "")).upper() == "APPROVED"
            score = float(event.get("score", 0.0) or 0.0)
            flaws = event.get("flaws") or []
            loop = event.get("loop", 0)
            verdict = "[bold green]✓ APPROVED[/bold green]" if approved else "[bold yellow]↻ REWORK REQUESTED[/bold yellow]"
            flaw_note = f" · {len(flaws)} critical flaw(s)" if flaws else ""
            self.console.print(
                f"  [bold cyan]⚖[/bold cyan] Loop {loop} consensus: "
                f"[bold]{score:.2f}/10[/bold]{flaw_note} ➔ {verdict}"
            )

        elif evt_type == "override.halt":
            reason = event.get("rationale", "Critical anomaly detected.")
            self.console.print(f"  [bold red]🛑 OVERRIDE HALT:[/bold red] {reason}")

        elif evt_type in ("youth.error", "elder.error"):
            label = "Youth" if evt_type == "youth.error" else "Elder"
            self.console.print(f"  [bold red]✗ {label} agent error:[/bold red] {event.get('error', 'unknown')}")

        elif evt_type == "circle.resolved":
            cost = float(event.get("total_cost_usd", 0.0) or 0.0)
            loops = event.get("loop_count", 0)
            self.console.print(
                f"  [bold green]🏁 Circle resolved[/bold green] [dim](loops: {loops} · spend: ${cost:.4f})[/dim]"
            )

        elif evt_type == "circle.escalated":
            status = event.get("status", "ESCALATED")
            warning = event.get("warning") or event.get("escalation_message") or ""
            self.console.print(f"  [bold yellow]⚠ {status}:[/bold yellow] {warning}")

        # ── Neuroplasticity events ───────────────────────────────────────
        elif evt_type == "plasticity.routing":
            tier = event.get("tier", "standard")
            complexity = float(event.get("complexity_score", 0.0) or 0.0)
            peer_model = event.get("peer", "?")
            memory_flag = "institutional memory injected" if event.get("memory_injected") else "no prior lessons"
            self.console.print(
                f"  [bold gold1]🧠[/bold gold1] Neuroplastic routing: "
                f"[bold]{tier}[/bold] tier [dim](complexity {complexity:.1f})[/dim] → peer "
                f"[cyan]{peer_model}[/cyan] · {memory_flag}"
            )

        elif evt_type == "plasticity.adapted":
            notes = event.get("notes") or []
            detail = "; ".join(notes[-2:]) if notes else f"peer → {event.get('peer', '?')}"
            self.console.print(f"  [bold gold1]🧠[/bold gold1] Adapting under stress: [italic]{detail}[/italic]")

        elif evt_type == "plasticity.complete":
            homeostasis = event.get("homeostasis") or {}
            weights = event.get("synaptic_weights") or {}
            stats = event.get("memory_stats") or {}
            threshold = homeostasis.get("approval_threshold", "?")
            w_sec = weights.get("security_governance")
            w_str = f"{w_sec:.2f}" if isinstance(w_sec, float) else "?"
            runs = stats.get("total_runs", 0)
            self.console.print(
                f"  [dim][gold1]🧠[/gold1] Learning updated: approval gate {threshold} · "
                f"security weight {w_str} · {runs} run(s) in experience memory[/dim]"
            )

        # ── Legacy uppercase events (kept for backward compatibility) ────
        elif evt_type == "AGENT_COMPLETED":
            agent_role = event.get("agent_role", "Agent")
            tokens = event.get("tokens_used", 0)
            cost = event.get("cost_usd", 0.0)
            self.console.print(f"  [green]✓[/green] [bold]{agent_role}[/bold] completed [dim]({tokens:,} tokens, ${cost:.4f})[/dim]")

        elif evt_type == "VERDICT_ISSUED":
            auditor = event.get("auditor", "Elder")
            approved = event.get("approved", False)
            score = event.get("score", 0.0)
            status_str = "[bold green]APPROVED[/bold green]" if approved else "[bold red]REWORK REQUESTED[/bold red]"
            self.console.print(f"  [magenta]👁[/magenta] [bold]{auditor}[/bold] Score: [bold]{score:.1f}/10.0[/bold] ➔ {status_str}")

        elif evt_type == "CONSENSUS_REACHED":
            approved = event.get("approved", False)
            score = event.get("score", 0.0)
            flaws = event.get("flaw_count", 0)
            status_str = "[bold green]CONSENSUS APPROVED[/bold green]" if approved else "[bold yellow]ITERATING DEBATE LOOP[/bold yellow]"
            self.console.print(f"  [bold cyan]⚖[/bold cyan] Final Weighted Score: [bold]{score:.2f}/10.0[/bold] (Flaws: {flaws}) ➔ {status_str}")

        elif evt_type == "OVERRIDE_CLEARED":
            self.console.print("  [bright_green]✓[/bright_green] Safety gate passed. No showstopper anomalies detected.")

        elif evt_type == "OVERRIDE_TRIGGERED":
            reason = event.get("reason", "Malicious or impossible constraint detected.")
            self.console.print(f"  [bold red]🛑 OVERRIDE HALT:[/bold red] {reason}")

        elif evt_type == "LOOP_INCREMENTED":
            loop = event.get("loop", 1)
            self.console.print(f"\n[bold yellow]↻ Entering Peer Revision Loop {loop}...[/bold yellow]")

    def render_deliverable(self, final_output: dict, output_dir: str = "./aztec_output") -> None:
        """Render syntax-highlighted deliverable code files and prompt to export."""
        deliverable = final_output.get("deliverable") or {}
        overview = deliverable.get("architecture_overview", "")
        code_files: Dict[str, str] = deliverable.get("implementation_code", {})
        mitigations: List[str] = deliverable.get("mitigations_applied", [])

        self.console.print()
        self.console.rule("[bold green]🏁 Aztec Circle Deliverable Summary[/bold green]", style="green")

        if overview:
            self.console.print(Panel(overview.strip(), title="[bold cyan]Architecture Overview[/bold cyan]", border_style="cyan"))

        if mitigations:
            mit_table = Table(title="Mitigations & Hardening Applied", header_style="bold yellow", expand=True)
            mit_table.add_column("#", width=4, style="dim")
            mit_table.add_column("Remediation / Mitigation", style="white")
            for idx, mit in enumerate(mitigations, start=1):
                mit_table.add_row(str(idx), mit)
            self.console.print(mit_table)

        if code_files:
            self.console.print(f"\n[bold green]📦 Generated Source Files ({len(code_files)}):[/bold green]")
            for filename, content in code_files.items():
                ext = filename.split(".")[-1] if "." in filename else "text"
                lexer = "python" if ext in ("py", "python") else "typescript" if ext in ("ts", "tsx") else "javascript" if ext in ("js", "jsx") else ext
                self.console.print(f"\n[bold cyan]─── File: {filename} ───[/bold cyan]")
                syntax = Syntax(content.strip(), lexer, theme="monokai", line_numbers=True, word_wrap=True)
                self.console.print(Panel(syntax, border_style="dim"))

            # Auto-save deliverable to disk with recursive directory creation
            os.makedirs(output_dir, exist_ok=True)
            saved_paths = []
            for filename, content in code_files.items():
                # Normalize filename and handle leading slashes
                clean_rel_path = filename.lstrip("/\\")
                out_path = os.path.join(output_dir, clean_rel_path)
                parent_dir = os.path.dirname(out_path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                try:
                    with open(out_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    saved_paths.append(out_path)
                except Exception as write_err:
                    self.console.print(f"  [bold red]Warning: Could not save file {out_path}:[/bold red] {write_err}")

            if saved_paths:
                self.console.print(f"\n[bold green]✓ Deliverable saved to directory:[/bold green] [underline]{output_dir}[/underline] ({len(saved_paths)} files written)")
                from aztec_circle.engine.scaffolder import scaffold_project
                scaffold_res = scaffold_project(output_dir)
                if scaffold_res.files_injected:
                    self.console.print(f"[bold green]✓ Auto-Scaffolded Project:[/bold green] Injected {len(scaffold_res.files_injected)} boilerplate configuration files: [dim]{', '.join(scaffold_res.files_injected)}[/dim]")

                from aztec_circle.engine.plan_manager import PlanManager
                plan_p = PlanManager.sync_from_codebase(output_dir)
                self.console.print(f"[bold green]✓ Living Blueprint Generated:[/bold green] [underline]{plan_p}[/underline]")
                self.console.print()
            else:
                self.console.print(f"\n[dim]No files written to {output_dir}.[/dim]\n")
