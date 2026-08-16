"""
Slash command engine and dispatchers for the Aztec interactive TUI.
"""

from __future__ import annotations

import sys
from typing import Callable, Coroutine, Dict, Tuple
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


async def cmd_models(args: str, state: SessionState, console: Console) -> None:
    """Display or change model assignments per agent rank."""
    parts = args.strip().split()
    if len(parts) >= 2:
        rank = parts[0].upper()
        model_name = parts[1]
        if rank in ("YOUTH", "PEER", "ELDER", "FALLBACK"):
            if rank == "YOUTH":
                settings.YOUTH_MODEL = model_name
            elif rank == "PEER":
                settings.PEER_MODEL = model_name
                state.primary_model = model_name
            elif rank == "ELDER":
                settings.ELDER_MODEL = model_name
            elif rank == "FALLBACK":
                settings.FALLBACK_MODEL = model_name
            console.print(f"[bold green]Updated {rank} model to:[/bold green] {model_name}")
            return
        else:
            console.print("[bold red]Invalid rank. Choose from: YOUTH, PEER, ELDER, FALLBACK[/bold red]")
            return

    table = Table(title="Aztec Agent Model Assignments", header_style="bold gold1", expand=True)
    table.add_column("Rank", style="bold cyan", width=12)
    table.add_column("Role / Responsibility", style="dim", width=36)
    table.add_column("Configured Model", style="bold green")

    table.add_row("Youth", "Chaos Brainstorming & Devil's Advocate (Parallel)", settings.YOUTH_MODEL)
    table.add_row("Peer", "Synthesis, Architecture & Code Drafting", settings.PEER_MODEL)
    table.add_row("Elder", "Security Governance & Structural Performance Council", settings.ELDER_MODEL)
    table.add_row("Fallback", "Provider Failover & Emergency Redirection", str(settings.FALLBACK_MODEL or "None"))

    console.print(table)
    console.print("[dim]Usage to update: /models <YOUTH|PEER|ELDER|FALLBACK> <model_name>[/dim]\n")


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


async def cmd_build(args: str, state: SessionState, console: Console) -> None:
    """Scaffold missing files, install dependencies, and build project with auto-repair."""
    from aztec_circle.engine.scaffolder import scaffold_project
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent

    target = args.strip() or state.output_dir
    console.print(f"[bold cyan]Scaffolding and building project at:[/bold cyan] {target}")
    scaffold_res = scaffold_project(target)
    if scaffold_res.files_injected:
        console.print(f"  [green]✓[/green] Injected {len(scaffold_res.files_injected)} boilerplate files: [dim]{', '.join(scaffold_res.files_injected)}[/dim]")

    runner = ProjectRunner(console=console)
    install_res = await runner.install_dependencies(scaffold_res.project_root)
    if install_res.success:
        build_res = await runner.build_project(scaffold_res.project_root)
        if not build_res.success:
            fixer = BuildFixAgent(console=console, max_iterations=2)
            await fixer.fix(scaffold_res.project_root, build_res, runner=runner)


async def cmd_fix(args: str, state: SessionState, console: Console) -> None:
    """Run automated build error fix loop on project."""
    from aztec_circle.engine.scaffolder import find_project_root
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent

    target = args.strip() or state.output_dir
    root = find_project_root(target)
    console.print(f"[bold cyan]Running Aztec Build Fixer on project at:[/bold cyan] {root}")
    runner = ProjectRunner(console=console)
    initial_build = await runner.build_project(root)

    if initial_build.success:
        console.print("[bold green]✓ Project is already building cleanly with zero errors![/bold green]\n")
        return

    fixer = BuildFixAgent(console=console, max_iterations=3)
    res = await fixer.fix(root, initial_build, runner=runner)
    state.record_cost(res.total_cost_usd)
    if res.success:
        console.print(f"[bold green]✓ Successfully repaired {len(res.patches_applied)} file(s) across {res.iterations} iteration(s)![/bold green]\n")
    else:
        console.print(f"[bold red]✗ Could not fully resolve all build errors after {res.iterations} iteration(s).[/bold red]\n")


async def cmd_test(args: str, state: SessionState, console: Console) -> None:
    """Run test suite for generated project."""
    from aztec_circle.engine.scaffolder import find_project_root
    from aztec_circle.engine.project_runner import ProjectRunner

    target = args.strip() or state.output_dir
    root = find_project_root(target)
    console.print(f"[bold cyan]Running test suite for project at:[/bold cyan] {root}")
    runner = ProjectRunner(console=console)
    await runner.test_project(root)


async def cmd_start(args: str, state: SessionState, console: Console) -> None:
    """Start live background development server."""
    from aztec_circle.engine.scaffolder import scaffold_project
    from aztec_circle.engine.project_runner import ProjectRunner

    target = args.strip() or state.output_dir
    scaffold_res = scaffold_project(target)
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
    console.print(f"[dim]Background dev server active on PID {server_proc.process.pid}. Use /stop to terminate.[/dim]\n")


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

    import os
    from aztec_circle.engine.patch_agent import PatchAgent
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent
    from aztec_circle.engine.scaffolder import find_project_root

    target_dir = state.output_dir
    # Auto-detect if target_dir doesn't exist but current directory is a project
    if not os.path.exists(target_dir) or target_dir == "./aztec_output":
        if os.path.exists("package.json") or os.path.exists("src"):
            target_dir = "."

    root = find_project_root(target_dir)
    agent = PatchAgent(console=console)
    res = await agent.run(instruction=instruction, project_dir=root, images=list(state.attached_images), verbose=True)

    if not res.success:
        console.print(f"[bold red]✗ Edit operation failed:[/bold red] {res.error_message or res.edit_summary}\n")
        return

    state.record_cost(res.total_cost_usd, res.round1_tokens + res.round2_tokens)
    console.print(f"\n[bold green]Summary:[/bold green] {res.edit_summary}")
    runner = ProjectRunner(console=console)
    tc_res = await runner.typecheck_project(root)
    if not tc_res.success:
        console.print("[yellow]Type check reported errors. Triggering atomic Build Fix Agent...[/yellow]")
        fixer = BuildFixAgent(console=console, max_iterations=2)
        fix_res = await fixer.fix(root, tc_res, runner=runner)
        state.record_cost(fix_res.total_cost_usd)
        if not fix_res.success:
            console.print("[bold red]Warning: Post-edit build check still has unresolved errors.[/bold red]\n")
    else:
        console.print("[bold green]✓ Type check passed with zero errors![/bold green]\n")


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

    await updater.perform_update()


COMMAND_HANDLERS: Dict[str, Callable[[str, SessionState, Console], Coroutine]] = {
    "/help": cmd_help,
    "/status": cmd_status,
    "/models": cmd_models,
    "/policy": cmd_policy,
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
