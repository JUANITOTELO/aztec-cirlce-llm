"""
Slash command engine and dispatchers for the Aztec interactive TUI.
"""

from __future__ import annotations

import json
import sys
from typing import Callable, Coroutine, Dict, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aztec_circle.config import settings
from aztec_circle.domain.models import FallbackPolicy
from aztec_circle.engine.checkpoint import CheckpointStore
from aztec_circle.tui.completer import SLASH_COMMAND_METADATA
from aztec_circle.tui.session import SessionState


async def cmd_help(args: str, state: SessionState, console: Console) -> None:
    """Display help table of slash commands and interactive guidance."""
    table = Table(title="Aztec Interactive TUI Commands", header_style="bold cyan", expand=True)
    table.add_column("Command", style="bold yellow", width=12)
    table.add_column("Description", style="white")

    for cmd, desc in SLASH_COMMAND_METADATA.items():
        table.add_row(cmd, desc)

    console.print(table)
    console.print("[dim]Tip: Enter any free-text prompt to run a full multi-generational Aztec debate.[/dim]\n")


async def cmd_status(args: str, state: SessionState, console: Console) -> None:
    """Display current session metrics, costs, and configuration."""
    table = Table(title="Aztec Session Status", header_style="bold magenta", expand=True)
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Session Spend", f"${state.total_cost_usd:.4f}")
    table.add_row("Total Tokens Consumed", f"{state.total_tokens:,}")
    table.add_row("Active Primary Model", state.primary_model)
    table.add_row("Budget Limit (Per Run)", f"${state.budget_limit_usd:.2f}")
    table.add_row("Max Debate Loops", str(state.max_loops))
    table.add_row("Fallback Policy", state.fallback_policy.value)
    table.add_row("Default Output Dir", state.output_dir)
    if state.active_task_id:
        table.add_row("Last Task ID", state.active_task_id)

    console.print(table)

    # ── Neuroplasticity section ─────────────────────────────────────────
    try:
        from aztec_circle.plasticity import PlasticityEngine

        if not settings.PLASTICITY_ENABLED:
            console.print("[dim]🧠 Neuroplasticity: disabled (PLASTICITY_ENABLED=false)[/dim]\n")
            return

        engine = PlasticityEngine()
        snap = engine.snapshot()
        h = snap["homeostasis"]
        w = snap["synaptic_weights"]
        m = snap["memory_stats"]

        p_table = Table(title="🧠 Neuroplastic State (learned across runs)", header_style="bold gold1", expand=True)
        p_table.add_column("Property", style="bold cyan")
        p_table.add_column("Value", style="green")

        gate = h.get("approval_threshold", settings.PLASTICITY_BASE_THRESHOLD)
        base = settings.PLASTICITY_BASE_THRESHOLD
        drift = gate - base
        arrow = "▲" if drift > 0 else "▼" if drift < 0 else "·"
        p_table.add_row("Approval Gate", f"{gate} [dim]({arrow}{abs(drift):.2f} vs base {base})[/dim]")
        p_table.add_row(
            "Flaw Penalty Multiplier",
            f"×{h.get('flaw_recurrence_multiplier', 1.0)}",
        )
        sec_w = w.get("security_governance")
        str_w = w.get("structural_perf")
        if isinstance(sec_w, float) and isinstance(str_w, float):
            p_table.add_row("Elder Synaptic Weights", f"security {sec_w:.2f} / structural {str_w:.2f}")
        p_table.add_row("Runs Learned", str(m.get("total_runs", 0)))
        p_table.add_row("Flaw Categories Remembered", str(m.get("distinct_flaw_categories", 0)))
        p_table.add_row("Avg Final Score (history)", str(m.get("avg_final_score", 0.0)))
        if snap.get("routing"):
            r = snap["routing"]
            p_table.add_row("Last Run Routing", f"{r.get('tier')} tier · peer {r.get('peer')}")
        console.print(p_table)
        engine.memory.close()
        console.print("[dim]Inspect details or reset learning with /plasticity[/dim]\n")
    except Exception as exc:
        console.print(f"[dim]🧠 Neuroplastic state unavailable: {exc}[/dim]\n")


async def cmd_plasticity(args: str, state: SessionState, console: Console) -> None:
    """Inspect or reset the neuroplastic learning subsystem: /plasticity [reset|lessons]"""
    from aztec_circle.plasticity import PlasticityEngine

    arg = args.strip().lower()

    if not settings.PLASTICITY_ENABLED:
        console.print("[yellow]Neuroplasticity is disabled.[/yellow] Set PLASTICITY_ENABLED=true to activate.")
        return

    engine = PlasticityEngine()

    if arg == "reset":
        before = engine.snapshot()["memory_stats"]
        engine.reset()
        engine.memory.close()
        console.print(
            "[bold green]✓ Metaplastic reset complete.[/bold green] "
            f"Forget everything learned from {before.get('total_runs', 0)} run(s); "
            "weights, thresholds, and experience memory restored to baseline."
        )
        return

    if arg == "lessons":
        recurring = engine.memory.top_recurring_flaws(limit=8)
        if not recurring:
            console.print("[dim]No flaw lessons recorded yet — the circle learns after each debate.[/dim]")
            engine.memory.close()
            return
        lessons = Table(title="📚 Lessons Learned (recurring flaw categories)", header_style="bold gold1", expand=True)
        lessons.add_column("Seen", justify="right", style="bold red", width=6)
        lessons.add_column("Recurring Flaw", style="white")
        lessons.add_column("Proven Fix / Mitigation", style="green")
        for item in recurring:
            occ = int(item.get("occurrences") or 0)
            detail = str(item.get("detail") or item.get("category") or "")
            mitigation = str(item.get("mitigation") or "") or "[dim]not yet solved[/dim]"
            lessons.add_row(f"{occ}×", detail[:160], mitigation[:160])
        console.print(lessons)
        engine.memory.close()
        return

    # Default: full snapshot
    snap = engine.snapshot()
    engine.memory.close()
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold cyan", width=22)
    grid.add_column(style="white")
    grid.add_row("Enabled", str(snap["enabled"]))
    grid.add_row("Synaptic Weights", ", ".join(f"{k}={v}" for k, v in snap["synaptic_weights"].items()))
    grid.add_row("Homeostasis", json.dumps(snap["homeostasis"]))
    grid.add_row("Memory Stats", json.dumps(snap["memory_stats"]))
    if snap.get("routing"):
        grid.add_row("Last Routing Plan", json.dumps(snap["routing"]))
    grid.add_row("State File", snap["state_path"])
    console.print(Panel(grid, title="[bold gold1]🧠 Neuroplastic Engine[/bold gold1]", border_style="gold1", expand=False))
    console.print("[dim]/plasticity lessons → view recurring flaw lessons · /plasticity reset → forget all learned state[/dim]")


async def cmd_config(args: str, state: SessionState, console: Console) -> None:
    """Open interactive configuration center or run subcommand: /config [keys|models|presets|test]"""
    from aztec_circle.tui.config_ui import (
        run_interactive_config_menu,
        render_api_keys_table,
        render_ranks_table,
        render_presets_table,
        run_test_models,
    )

    arg = args.strip().lower()
    if not arg:
        await run_interactive_config_menu(console, state)
        return

    if arg.startswith("key"):
        render_api_keys_table(console)
    elif arg.startswith("model"):
        render_ranks_table(console)
    elif arg.startswith("preset"):
        render_presets_table(console)
    elif arg.startswith("test"):
        await run_test_models(console)
    else:
        await run_interactive_config_menu(console, state)


async def cmd_keys(args: str, state: SessionState, console: Console) -> None:
    """View or set API keys: /keys or /keys <KEY_NAME> <KEY_VALUE>"""
    from aztec_circle.engine.config_manager import ConfigManager
    from aztec_circle.tui.config_ui import render_api_keys_table

    parts = args.strip().split(maxsplit=1)
    if len(parts) == 2:
        k_name, k_val = parts[0].upper(), parts[1].strip()
        ConfigManager.save_api_key(k_name, k_val)
        console.print(f"[bold green]✓ Successfully updated and saved {k_name} to ~/.aztec/config.env[/bold green]\n")
        return

    render_api_keys_table(console)
    console.print("[dim]Usage to update: /keys <KEY_NAME> <KEY_VALUE>  (e.g., /keys GEMINI_API_KEY AIzaSy...)[/dim]\n")


async def _render_discovered_table(
    console: Console,
    search: Optional[str] = None,
    provider: Optional[str] = None,
    local_only: bool = False,
    limit: int = 40,
) -> None:
    """Render a table of dynamically-discovered models (cache-backed, offline-safe)."""
    from aztec_circle.adapters.model_discovery import unified_catalog

    models = unified_catalog(provider=provider, search=search, include_curated=not local_only)
    if local_only:
        models = [m for m in models if m.provider in ("ollama", "lmstudio", "llamacpp")]

    if not models:
        console.print("[yellow]No models found.[/yellow] Run [bold]/models refresh[/bold] to discover OpenRouter + local models.")
        return

    title = "🔎 Discovered Models"
    if search:
        title += f" — matching '{search}'"
    table = Table(title=title, header_style="bold cyan", expand=True)
    table.add_column("Model ID (assignable)", style="white", overflow="fold")
    table.add_column("Prov.", style="magenta", width=11)
    table.add_column("Ctx k", justify="right", width=7)
    table.add_column("$in/M", justify="right", width=8)
    table.add_column("$out/M", justify="right", width=8)
    table.add_column("Caps", width=6)
    table.add_column("Suggested Ranks", style="dim", overflow="fold")

    def _fmt_cost(v: float) -> str:
        return "[green]free[/green]" if v <= 0 else f"{v:.2f}"

    for m in models[:limit]:
        caps = "".join([
            "V" if m.multimodal else "·",
            "R" if m.reasoning else "·",
        ])
        table.add_row(
            f"{m.id}",
            m.provider,
            str(m.context_k) if m.context_k else "—",
            _fmt_cost(m.input_cost_per_m),
            _fmt_cost(m.output_cost_per_m),
            caps,
            "/".join(m.recommended_ranks),
        )

    console.print(table)
    shown = min(len(models), limit)
    console.print(f"[dim]{shown} of {len(models)} models · Caps: V=vision R=reasoning · assign with /models <ROLE> <MODEL_ID>[/dim]\n")


async def cmd_models(args: str, state: SessionState, console: Console) -> None:
    """Display or change model assignments per agent rank/role: /models, /models <ROLE> <MODEL_ID>, /models reset <ROLE>, or /models pick"""
    from aztec_circle.engine.config_manager import ConfigManager
    from aztec_circle.tui.config_ui import render_ranks_table, render_model_catalog_table, run_interactive_role_picker

    text = args.strip()
    parts = text.split()

    if text.lower() in ("pick", "select", "choose", "wizard"):
        await run_interactive_role_picker(console, state)
        return

    if text.lower() in ("catalog", "all", "list"):
        render_model_catalog_table(console)
        return

    # ── Dynamic model discovery subcommands ──────────────────────────────
    if text.lower() == "refresh":
        from aztec_circle.adapters.model_discovery import refresh_all
        console.print("[bold cyan]🔎 Discovering models…[/bold cyan] [dim](OpenRouter · Ollama · LM Studio · llama.cpp)[/dim]")
        statuses = await refresh_all(force=True)
        for source, status_str in statuses.items():
            icon = "✓" if "unavailable" not in status_str else "○"
            style = "green" if "unavailable" not in status_str else "dim"
            console.print(f"  [{style}]{icon} {source}: {status_str}[/{style}]")
        total = sum(int(s.split()[0]) for s in statuses.values() if "unavailable" not in s)
        console.print(f"\n[bold green]✓ {total} live models cached.[/bold green] Browse with [bold]/models search <query>[/bold], [bold]/models local[/bold], or [bold]/models openrouter[/bold].\n")
        return

    if parts and parts[0].lower() == "search":
        query = " ".join(parts[1:])
        await _render_discovered_table(console, search=query or None)
        return

    if text.lower() in ("local", "ollama", "lmstudio", "llamacpp", "offline"):
        await _render_discovered_table(console, local_only=True)
        return

    if parts and parts[0].lower() == "openrouter":
        query = " ".join(parts[1:]) or None
        await _render_discovered_table(console, provider="openrouter", search=query)
        return

    if len(parts) >= 2:
        subcmd = parts[0].lower()
        if subcmd in ("reset", "unset", "clear"):
            target_role = parts[1]
            ConfigManager.reset_model_assignment(target_role)
            console.print(f"[bold green]✓ Reset {target_role.upper()} to inherit from rank default.[/bold green]\n")
            return
        elif subcmd in ("set", "assign") and len(parts) >= 3:
            role = parts[1]
            model_name = parts[2]
            ConfigManager.save_model_assignment(role, model_name)
            if role.upper() in ("PEER", "PEER_MODEL"):
                state.primary_model = model_name
            console.print(f"[bold green]✓ Updated and saved {role.upper()} model to:[/bold green] {model_name}\n")
            return
        else:
            role = parts[0]
            model_name = parts[1]
            ConfigManager.save_model_assignment(role, model_name)
            if role.upper() in ("PEER", "PEER_MODEL"):
                state.primary_model = model_name
            console.print(f"[bold green]✓ Updated and saved {role.upper()} model to:[/bold green] {model_name}\n")
            return

    render_ranks_table(console)
    console.print("[dim]Assign: /models <ROLE_KEY> <model_name>  (e.g., /models ELDER_SECURITY deepseek/deepseek-r1)[/dim]")
    console.print("[dim]Picker: /models pick                     (interactive numbered model menu)[/dim]")
    console.print("[dim]Reset:  /models reset <ROLE_KEY>         (revert sub-role to inherit from rank)[/dim]")
    console.print("[dim]Catalog:/models catalog                  (view capabilities & pricing across providers)[/dim]\n")



async def cmd_preset(args: str, state: SessionState, console: Console) -> None:
    """Apply an architecture preset: /preset <speed_budget|max_reasoning|google_suite|openai_suite|local_offline>"""
    from aztec_circle.domain.model_catalog import PRESET_CONFIGURATIONS
    from aztec_circle.engine.config_manager import ConfigManager
    from aztec_circle.tui.config_ui import render_presets_table

    preset_id = args.strip().lower()
    if not preset_id:
        render_presets_table(console)
        return

    if preset_id in PRESET_CONFIGURATIONS:
        ConfigManager.apply_preset(preset_id)
        state.primary_model = settings.PEER_MODEL
        console.print(f"[bold green]✓ Successfully applied preset:[/bold green] {PRESET_CONFIGURATIONS[preset_id]['name']}")
        console.print(f"[dim]{PRESET_CONFIGURATIONS[preset_id]['description']}[/dim]\n")
    else:
        console.print(f"[bold red]Unknown preset '{preset_id}'.[/bold red]")
        render_presets_table(console)


async def cmd_test_models(args: str, state: SessionState, console: Console) -> None:
    """Probe active rank models with a live 1-token test ping."""
    from aztec_circle.tui.config_ui import run_test_models
    await run_test_models(console)


async def cmd_policy(args: str, state: SessionState, console: Console) -> None:
    """Set or view the debate fallback policy."""
    arg = args.strip().upper()
    if arg:
        try:
            state.fallback_policy = FallbackPolicy(arg)
            console.print(f"[bold green]Fallback policy updated to:[/bold green] {state.fallback_policy.value}")
            return
        except ValueError:
            valid = [p.value for p in FallbackPolicy]
            console.print(f"[bold red]Invalid policy '{arg}'. Valid options: {', '.join(valid)}[/bold red]")
            return

    console.print(f"[bold cyan]Current Fallback Policy:[/bold cyan] {state.fallback_policy.value}")
    console.print("[dim]Valid options: HUMAN_IN_THE_LOOP, BEST_EFFORT_RELEASE, ABORT[/dim]")
    console.print("[dim]Usage: /policy <POLICY_NAME>[/dim]\n")


async def cmd_budget(args: str, state: SessionState, console: Console) -> None:
    """Set or display the maximum per-run USD budget limit: /budget [amount]"""
    from aztec_circle.engine.config_manager import ConfigManager

    raw = args.strip().lstrip("$")
    if not raw:
        console.print(f"[bold cyan]Current Budget Limit (Per Run):[/bold cyan] [bold green]${state.budget_limit_usd:.2f}[/bold green]")
        console.print(f"[dim]Total Session Spend: ${state.total_cost_usd:.4f} ({state.total_tokens:,} tokens)[/dim]")
        console.print("[dim]To set, use: [bold yellow]/budget <amount>[/bold yellow] (e.g. /budget 2.50, /budget 5, /budget 0.50)[/dim]\n")
        return

    try:
        new_budget = float(raw)
        if new_budget <= 0:
            console.print("[bold red]Budget must be a positive number greater than 0.[/bold red]\n")
            return

        state.budget_limit_usd = new_budget
        ConfigManager.save_api_key("BUDGET_LIMIT_USD", f"{new_budget:.2f}")
        console.print(f"[bold green]✓ Updated per-run budget limit to:[/bold green] [bold white]${new_budget:.2f}[/bold white]\n")

    except ValueError:
        console.print(f"[bold red]Invalid budget amount '{raw}'. Example: /budget 2.00 or /budget 5[/bold red]\n")


async def cmd_runs(args: str, state: SessionState, console: Console) -> None:
    """List historical task runs from the SQLite checkpoint store."""
    store = CheckpointStore()
    runs = await store.list_runs()
    if not runs:
        console.print("[dim]No historical runs found in checkpoint database.[/dim]")
        return

    table = Table(title="Aztec Checkpointed Runs", header_style="bold cyan", expand=True)
    table.add_column("Task ID", style="dim", width=10)
    table.add_column("Phase", style="bold magenta", width=18)
    table.add_column("Loops", justify="center", width=8)
    table.add_column("Cost ($)", justify="right", width=10)
    table.add_column("Updated At", width=20)
    table.add_column("Goal", style="white")

    for r in runs:
        table.add_row(
            str(r.get("task_id", ""))[:8],
            str(r.get("phase", "")),
            str(r.get("loops", 0)),
            f"${float(r.get('cost_usd', 0.0)):.4f}",
            str(r.get("updated_at", ""))[:19],
            str(r.get("goal", ""))[:50],
        )

    console.print(table)
    console.print("[dim]Tip: Resume any run with /resume <task_id>[/dim]\n")


async def cmd_resume(args: str, state: SessionState, console: Console) -> None:
    """Resume a previous checkpointed task."""
    task_id = args.strip()
    if not task_id:
        console.print("[bold red]Please specify a task ID. Usage: /resume <task_id>[/bold red]")
        return

    store = CheckpointStore()
    loaded_state = await store.load(task_id)
    if not loaded_state:
        # Try matching prefix
        all_runs = await store.list_runs()
        matches = [r for r in all_runs if r.get("task_id", "").startswith(task_id)]
        if matches:
            full_id = matches[0]["task_id"]
            loaded_state = await store.load(full_id)
        else:
            console.print(f"[bold red]No checkpoint found matching task ID: {task_id}[/bold red]")
            return

    console.print(f"[bold green]Resuming task {loaded_state.task_id[:8]} from phase {loaded_state.current_phase.value}...[/bold green]")
    state.active_task_id = loaded_state.task_id


def _resolve_target_dir(state: SessionState, explicit_target: str = "") -> str:
    """Auto-discover canonical project root from explicit input or session state."""
    from aztec_circle.engine.scaffolder import find_project_root
    target = explicit_target.strip() or state.output_dir
    return find_project_root(target)


async def cmd_build(args: str, state: SessionState, console: Console) -> None:
    """Scaffold missing files, install dependencies, and build project with auto-repair."""
    from aztec_circle.engine.scaffolder import scaffold_project
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent

    target = _resolve_target_dir(state, args)
    console.print(f"[bold cyan]Scaffolding and building project at:[/bold cyan] {target}")
    scaffold_res = scaffold_project(target)
    if scaffold_res.files_injected:
        console.print(f"  [green]✓[/green] Injected {len(scaffold_res.files_injected)} boilerplate files: [dim]{', '.join(scaffold_res.files_injected)}[/dim]")

    runner = ProjectRunner(console=console)
    install_res = await runner.install_dependencies(scaffold_res.project_root)
    if install_res.success:
        build_res = await runner.build_project(scaffold_res.project_root)
        if not build_res.success:
            fixer = BuildFixAgent(console=console, max_iterations=3)
            fix_res = await fixer.fix(scaffold_res.project_root, build_res, runner=runner)
            state.record_cost(fix_res.total_cost_usd)


async def cmd_fix(args: str, state: SessionState, console: Console) -> None:
    """Run automated build error fix loop on project."""
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent

    root = _resolve_target_dir(state, args)
    console.print(f"[bold cyan]Running Aztec Build Fixer on project at:[/bold cyan] {root}")
    runner = ProjectRunner(console=console)

    server_err_res = None
    if state.active_server:
        server_err_res = runner.drain_server_errors(state.active_server)

    initial_build = await runner.verify_project_smart(root, force_full_build=True)

    combined_fail = None
    if not initial_build.success:
        combined_fail = initial_build
    elif server_err_res and not server_err_res.success:
        combined_fail = server_err_res
    else:
        # Check if project test suites pass
        test_res = await runner.test_project(root)
        if not test_res.success:
            combined_fail = test_res

    if not combined_fail:
        console.print("[bold green]✓ Project is already building and passing tests cleanly with zero errors![/bold green]\n")
        return

    fixer = BuildFixAgent(console=console, max_iterations=3)
    res = await fixer.fix(
        root,
        combined_fail,
        runner=runner,
        verify_fn=lambda r: runner.verify_project_comprehensive(r, include_tests=True),
    )
    state.record_cost(res.total_cost_usd)
    if res.success:
        console.print(f"[bold green]✓ Successfully repaired {len(res.patches_applied)} file(s) across {res.iterations} iteration(s)![/bold green]\n")
    else:
        console.print(f"[bold red]✗ Could not fully resolve all build errors after {res.iterations} iteration(s).[/bold red]\n")


async def cmd_test(args: str, state: SessionState, console: Console) -> None:
    """Run test suite for generated project."""
    from aztec_circle.engine.project_runner import ProjectRunner

    root = _resolve_target_dir(state, args)
    console.print(f"[bold cyan]Running test suite for project at:[/bold cyan] {root}")
    runner = ProjectRunner(console=console)
    await runner.test_project(root)


async def cmd_start(args: str, state: SessionState, console: Console) -> None:
    """Start live background development server."""
    from aztec_circle.engine.scaffolder import scaffold_project
    from aztec_circle.engine.project_runner import ProjectRunner

    root = _resolve_target_dir(state, args)
    scaffold_res = scaffold_project(root)
    runner = ProjectRunner(console=console)

    if state.active_server:
        console.print("[yellow]Stopping existing dev server process...[/yellow]")
        await state.active_server.stop()
        state.active_server = None

    install_res = await runner.install_dependencies(scaffold_res.project_root)
    if not install_res.success:
        console.print("[bold red]Dependency installation failed. Aborting dev server start.[/bold red]")
        return

    server_proc = await runner.start_dev_server(scaffold_res.project_root, port=5173)
    state.active_server = server_proc
    console.print(f"[dim]Background dev server active on PID {server_proc.process.pid}. Use /stop to terminate, /logs to inspect.[/dim]\n")


async def cmd_logs(args: str, state: SessionState, console: Console) -> None:
    """View background development server logs: /logs [num_lines]"""
    import os

    root = _resolve_target_dir(state)
    log_file = os.path.join(root, ".aztec_server.log")

    if not os.path.exists(log_file):
        console.print("[dim]No dev server log file found. Start the server with /start first.[/dim]\n")
        return

    num_lines = 30
    if args.strip().isdigit():
        num_lines = int(args.strip())

    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        tail = lines[-num_lines:]
        console.print(f"[bold cyan]Server Logs ({os.path.basename(log_file)} - last {len(tail)} lines):[/bold cyan]")
        for l in tail:
            console.print(f"  [dim]{l.rstrip()}[/dim]")
        console.print()
    except Exception as exc:
        console.print(f"[bold red]Failed to read server logs:[/bold red] {exc}\n")


async def cmd_stop(args: str, state: SessionState, console: Console) -> None:
    """Stop active background dev server."""
    if state.active_server:
        await state.active_server.stop()
        state.active_server = None
        console.print("[bold green]✓ Background development server stopped.[/bold green]\n")
    else:
        console.print("[dim]No active development server running.[/dim]\n")


async def cmd_clear(args: str, state: SessionState, console: Console) -> None:
    """Clear the terminal screen."""
    console.clear()


async def cmd_exit(args: str, state: SessionState, console: Console) -> None:
    """Exit the interactive session."""
    if state.active_server:
        await state.active_server.stop()
        state.active_server = None
    console.print("[bold yellow]Exiting Aztec session. Goodbye![/bold yellow]")
    sys.exit(0)


async def cmd_edit(args: str, state: SessionState, console: Console) -> None:
    """Apply atomic targeted edit to current project."""
    instruction = args.strip()
    if not instruction:
        console.print("[yellow]Usage: /edit <instruction e.g. 'Add a screenshot button'>[/yellow]\n")
        return

    from aztec_circle.engine.patch_agent import PatchAgent
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent

    root = _resolve_target_dir(state)
    agent = PatchAgent(console=console)
    res = await agent.run(instruction=instruction, project_dir=root, images=list(state.attached_images), verbose=True)

    if not res.success:
        console.print(f"[bold red]✗ Edit operation failed:[/bold red] {res.error_message or res.edit_summary}\n")
        return

    state.record_cost(res.total_cost_usd, res.round1_tokens + res.round2_tokens)
    console.print(f"\n[bold green]Summary:[/bold green] {res.edit_summary}")
    runner = ProjectRunner(console=console)
    gate_res = await runner.verify_project_smart(root)
    if not gate_res.success:
        if BuildFixAgent.is_recoverable(gate_res.stderr + gate_res.stdout):
            console.print("[yellow]Build verification reported errors. Triggering atomic Build Fix Agent...[/yellow]")
            fixer = BuildFixAgent(console=console, max_iterations=3)
            fix_res = await fixer.fix(root, gate_res, runner=runner)
            state.record_cost(fix_res.total_cost_usd)
            if not fix_res.success:
                console.print("[bold red]Warning: Post-edit build check still has unresolved errors.[/bold red]\n")
            else:
                console.print(f"[bold green]✓ Build healed successfully in {fix_res.iterations} iteration(s)![/bold green]\n")
        else:
            console.print("[bold yellow]⚠ Unrecoverable build error detected. Use /fix for details.[/bold yellow]\n")
    else:
        console.print("[bold green]✓ Quality gate passed cleanly with zero errors![/bold green]\n")

    if state.active_server:
        srv_errs = runner.drain_server_errors(state.active_server)
        if srv_errs and not srv_errs.success and BuildFixAgent.is_recoverable(srv_errs.stderr):
            console.print("[yellow]Live server reported runtime errors. Auto-healing...[/yellow]")
            fixer = BuildFixAgent(console=console, max_iterations=2)
            fix_res = await fixer.fix(root, srv_errs, runner=runner)
            state.record_cost(fix_res.total_cost_usd)


async def cmd_rebuild(args: str, state: SessionState, console: Console) -> None:
    """Force a full debate cycle to regenerate project from scratch."""
    goal = args.strip() or state.last_goal
    if not goal:
        console.print("[yellow]Usage: /rebuild <goal description>[/yellow]\n")
        return

    from aztec_circle.tui.interactive import run_debate_session
    from aztec_circle.tui.renderer import TranscriptRenderer
    renderer = TranscriptRenderer(console)
    await run_debate_session(goal, state, renderer)


async def cmd_paste(args: str, state: SessionState, console: Console) -> None:
    """Grab and attach an image directly from the system clipboard."""
    from aztec_circle.adapters.clipboard_utils import get_clipboard_image
    from aztec_circle.adapters.image_utils import encode_image_to_data_uri

    clip_img = get_clipboard_image()
    if not clip_img:
        console.print("[yellow]No image data found in system clipboard.[/yellow] [dim](Copy a screenshot/image first, or use /image <path>)[/dim]\n")
        return

    try:
        data_uri = encode_image_to_data_uri(clip_img)
        state.attached_images.append(data_uri)
        console.print(f"[bold green]✓ Attached clipboard image:[/bold green] [underline]{clip_img}[/underline] [dim](Total attached: {len(state.attached_images)})[/dim]\n")
    except Exception as exc:
        console.print(f"[bold red]✗ Failed to process clipboard image:[/bold red] {exc}\n")


async def cmd_image(args: str, state: SessionState, console: Console) -> None:
    """Attach reference image to the active session: /image <path_or_url> or /image paste"""
    target = args.strip()
    if not target or target.lower() in ("paste", "clip"):
        await cmd_paste("", state, console)
        return

    from aztec_circle.adapters.clipboard_utils import clean_image_path
    from aztec_circle.adapters.image_utils import encode_image_to_data_uri

    cleaned_target = clean_image_path(target)
    try:
        data_uri = encode_image_to_data_uri(cleaned_target)
        state.attached_images.append(data_uri)
        console.print(f"[bold green]✓ Attached reference image:[/bold green] [underline]{cleaned_target}[/underline] [dim](Total attached: {len(state.attached_images)})[/dim]\n")
    except Exception as exc:
        console.print(f"[bold red]✗ Failed to attach image:[/bold red] {exc}\n")


async def cmd_images(args: str, state: SessionState, console: Console) -> None:
    """List all attached reference images in the active session."""
    if not state.attached_images:
        console.print("[dim]No reference images attached to active session. Use /image <path> to add.[/dim]\n")
        return
    console.print(f"[bold cyan]Attached Reference Images ({len(state.attached_images)}):[/bold cyan]")
    for idx, img in enumerate(state.attached_images, start=1):
        preview = img[:60] + "..." if len(img) > 60 else img
        console.print(f"  {idx}. [dim]{preview}[/dim]")
    console.print()


async def cmd_clear_images(args: str, state: SessionState, console: Console) -> None:
    """Remove all attached images from the active session."""
    count = len(state.attached_images)
    state.attached_images.clear()
    console.print(f"[green]✓ Cleared {count} attached image(s) from session.[/green]\n")


async def cmd_update(args: str, state: SessionState, console: Console) -> None:
    """Check for and apply latest Aztec framework updates."""
    from aztec_circle.engine.updater import AztecUpdater
    updater = AztecUpdater(console=console)
    check_only = "--check" in args or "-c" in args
    if check_only:
        res = updater.check_for_updates()
        if res.has_update:
            console.print(f"[bold yellow]Update available:[/bold yellow] {res.message}")
            console.print("Run [bold cyan]/update[/bold cyan] to install.\n")
        else:
            console.print(f"[green]✓ {res.message}[/green] [dim](current: v{res.current_version})[/dim]\n")
        return

async def cmd_plan(args: str, state: SessionState, console: Console) -> None:
    """Display, synchronize, inspect, or build a new module into the living project blueprint (AZTEC_PLAN.md)."""
    from aztec_circle.engine.plan_manager import PlanManager

    target_dir = state.output_dir or "."
    raw_args = args.strip()
    subcmd = raw_args.lower()

    if subcmd == "sync":
        p = PlanManager.sync_from_codebase(target_dir, goal=state.last_goal)
        console.print(f"[bold green]✓ Synchronized Living Blueprint from source codebase:[/bold green] [underline]{p}[/underline]\n")
        PlanManager.render_plan_dashboard(target_dir, console)
    elif subcmd == "file":
        p = PlanManager.get_plan_path(target_dir)
        console.print(f"[bold cyan]Plan File Path:[/bold cyan] {p} [dim](Exists: {p.exists()})[/dim]\n")
    elif not raw_args or subcmd in ("view", "show", "dashboard"):
        PlanManager.render_plan_dashboard(target_dir, console)
    else:
        # User entered a module description / goal e.g. "/plan We would like to create a new module..."
        from aztec_circle.tui.interactive import run_modular_consensus_session
        await run_modular_consensus_session(raw_args, state, console)


async def cmd_roadmap(args: str, state: SessionState, console: Console) -> None:
    """Display implementation roadmap & milestone progress from AZTEC_PLAN.md."""
    from aztec_circle.engine.plan_manager import PlanManager

    target_dir = state.output_dir or "."
    PlanManager.render_plan_dashboard(target_dir, console)


async def cmd_consensus(args: str, state: SessionState, console: Console) -> None:
    """Run multi-generational consensus debate to architect and build a new module: /consensus <goal>"""
    raw_args = args.strip()
    if not raw_args:
        console.print("[yellow]Usage: /consensus <module or feature description e.g. 'Add product management module'>[/yellow]\n")
        return

    from aztec_circle.tui.interactive import run_modular_consensus_session
    await run_modular_consensus_session(raw_args, state, console)
async def cmd_clean(args: str, state: SessionState, console: Console):
    """Clean development ports and temporary workspace artifacts."""
    from aztec_circle.engine.project_runner import free_ports
    target_ports = list(range(5173, 5186)) + list(range(8000, 8016))
    freed = free_ports(target_ports)
    if freed:
        console.print(f"[bold green]✓ Freed occupied server ports:[/bold green] {', '.join(str(p) for p in freed)}\n")
    else:
        console.print("[dim]No lingering server processes found on development ports (5173–5185, 8000–8015).[/dim]\n")


async def cmd_run(args: str, state: SessionState, console: Console) -> None:
    """Execute console/shell command in project directory with streaming output: /run <command>"""
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.scaffolder import find_project_root
    from aztec_circle.engine.plan_manager import PlanManager

    cmd_str = args.strip()
    if not cmd_str:
        console.print("[yellow]Usage: /run <shell command> (e.g., /run ls -la, /run npm list)[/yellow]\n")
        return

    target = state.output_dir or "."
    root = find_project_root(target) or target

    runner = ProjectRunner(console=console)
    await runner.run_shell_command_streamed(cmd_str=cmd_str, cwd=root, title="Console Command")

    if PlanManager.plan_exists(root):
        PlanManager.record_edit_iteration(
            output_dir=root,
            instruction=f"Interactive Shell: {cmd_str}",
            modified_files=[],
            executed_commands=[cmd_str],
        )


async def cmd_php(args: str, state: SessionState, console: Console) -> None:
    """Execute PHP script or command in project directory: /php <args>"""
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.scaffolder import find_project_root
    from aztec_circle.engine.plan_manager import PlanManager

    raw_args = args.strip() or "-v"
    cmd_str = f"php {raw_args}"
    target = state.output_dir or "."
    root = find_project_root(target) or target

    runner = ProjectRunner(console=console)
    await runner.run_shell_command_streamed(cmd_str=cmd_str, cwd=root, title="PHP Execution")

    if PlanManager.plan_exists(root) and raw_args != "-v":
        PlanManager.record_edit_iteration(
            output_dir=root,
            instruction=f"PHP Command: {cmd_str}",
            modified_files=[],
            executed_commands=[cmd_str],
        )


async def cmd_mysql(args: str, state: SessionState, console: Console) -> None:
    """Execute MySQL command or script: /mysql <args>"""
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.scaffolder import find_project_root
    from aztec_circle.engine.plan_manager import PlanManager

    raw_args = args.strip()
    if not raw_args:
        console.print("[yellow]Usage: /mysql <args> (e.g., /mysql -u root -p database < schema.sql)[/yellow]\n")
        return

    cmd_str = f"mysql {raw_args}"
    target = state.output_dir or "."
    root = find_project_root(target) or target

    runner = ProjectRunner(console=console)
    await runner.run_shell_command_streamed(cmd_str=cmd_str, cwd=root, title="MySQL Execution")

    if PlanManager.plan_exists(root):
        PlanManager.record_edit_iteration(
            output_dir=root,
            instruction=f"MySQL Command: {cmd_str}",
            modified_files=[],
            executed_commands=[cmd_str],
        )


async def cmd_sqlite(args: str, state: SessionState, console: Console) -> None:
    """Execute SQLite query or script against project database: /sqlite [db_file] <query_or_file>"""
    import os
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.scaffolder import find_project_root
    from aztec_circle.engine.plan_manager import PlanManager

    raw_args = args.strip()
    target = state.output_dir or "."
    root = find_project_root(target) or target

    # Check for existing SQLite db file candidates in project
    db_candidates = [
        "database.sqlite",
        "app.db",
        "backend/database.sqlite",
        "backend/app.db",
        "data.sqlite",
        "db.sqlite",
    ]
    detected_db = None
    for cand in db_candidates:
        cand_path = os.path.join(root, cand)
        if os.path.exists(cand_path):
            detected_db = cand
            break

    if not raw_args:
        if detected_db:
            cmd_str = f"sqlite3 {detected_db} .tables"
        else:
            console.print("[yellow]Usage: /sqlite <database.sqlite> <query or commands> (e.g. /sqlite database.sqlite .schema)[/yellow]\n")
            return
    else:
        parts = raw_args.split(maxsplit=1)
        if parts[0].endswith((".sqlite", ".db", ".sqlite3")) or os.path.exists(os.path.join(root, parts[0])):
            cmd_str = f"sqlite3 {raw_args}"
        elif detected_db:
            cmd_str = f"sqlite3 {detected_db} {raw_args}"
        else:
            cmd_str = f"sqlite3 {raw_args}"

    runner = ProjectRunner(console=console)
    await runner.run_shell_command_streamed(cmd_str=cmd_str, cwd=root, title="SQLite Execution")

    if PlanManager.plan_exists(root):
        PlanManager.record_edit_iteration(
            output_dir=root,
            instruction=f"SQLite Command: {cmd_str}",
            modified_files=[],
            executed_commands=[cmd_str],
        )


COMMAND_HANDLERS: Dict[str, Callable[[str, SessionState, Console], Coroutine]] = {
    "/help": cmd_help,
    "/status": cmd_status,
    "/plasticity": cmd_plasticity,
    "/plan": cmd_plan,
    "/roadmap": cmd_roadmap,
    "/consensus": cmd_consensus,
    "/module": cmd_consensus,
    "/feature": cmd_consensus,
    "/debate": cmd_consensus,
    "/circle": cmd_consensus,
    "/config": cmd_config,
    "/setup": cmd_config,
    "/keys": cmd_keys,
    "/preset": cmd_preset,
    "/presets": cmd_preset,
    "/test-models": cmd_test_models,
    "/models": cmd_models,
    "/policy": cmd_policy,
    "/budget": cmd_budget,
    "/runs": cmd_runs,
    "/resume": cmd_resume,
    "/build": cmd_build,
    "/edit": cmd_edit,
    "/rebuild": cmd_rebuild,
    "/image": cmd_image,
    "/paste": cmd_paste,
    "/paste-image": cmd_paste,
    "/clip": cmd_paste,
    "/images": cmd_images,
    "/clear-images": cmd_clear_images,
    "/update": cmd_update,
    "/fix": cmd_fix,
    "/test": cmd_test,
    "/start": cmd_start,
    "/stop": cmd_stop,
    "/run": cmd_run,
    "/sh": cmd_run,
    "/exec": cmd_run,
    "/cmd": cmd_run,
    "/php": cmd_php,
    "/mysql": cmd_mysql,
    "/sqlite": cmd_sqlite,
    "/db": cmd_sqlite,
    "/clean": cmd_clean,
    "/ports": cmd_clean,
    "/free-ports": cmd_clean,
    "/logs": cmd_logs,
    "/server-logs": cmd_logs,
    "/clear": cmd_clear,
    "/exit": cmd_exit,
    "/quit": cmd_exit,
}


async def dispatch_slash_command(raw_input: str, state: SessionState, console: Console) -> bool:
    """
    Check if the input starts with a slash command and dispatch to the appropriate handler.
    Returns True if handled as a command, False if it is a free-text goal.
    """
    text = raw_input.strip()
    if not text.startswith("/"):
        return False

    parts = text.split(maxsplit=1)
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    handler = COMMAND_HANDLERS.get(cmd)
    if handler:
        await handler(args, state, console)
    else:
        console.print(f"[bold red]Unknown command '{cmd}'. Type /help for available commands.[/bold red]\n")

    return True
