"""
CLI entry point for Aztec Decision Circle.
"""

from __future__ import annotations

import asyncio
import re
from typing import List, Optional
import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from aztec_circle.domain.models import CircleRunState, FallbackPolicy
from aztec_circle.engine.checkpoint import CheckpointStore
from aztec_circle.engine.state_machine import AztecOrchestrator

app = typer.Typer(
    name="aztec",
    help="Aztec Decision Circle: Multi-Generational Adversarial LLM Debate Framework",
    no_args_is_help=False,
)
console = Console()


def version_callback(value: bool):
    if value:
        import aztec_circle
        console.print(f"[bold cyan]Aztec Decision Circle[/bold cyan] [green]v{aztec_circle.__version__}[/green]")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        help="Show Aztec version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
):
    """If no subcommand is passed, launch the interactive agy-style Aztec TUI."""
    from aztec_circle.engine.config_manager import ConfigManager
    ConfigManager.load_config_into_env()

    if ctx.invoked_subcommand is None:
        from aztec_circle.tui.interactive import start_interactive_session
        asyncio.run(start_interactive_session())


@app.command("interactive")
def interactive():
    """
    Launch the interactive agy-style Aztec TUI session.
    """
    from aztec_circle.tui.interactive import start_interactive_session
    asyncio.run(start_interactive_session())


@app.command()
def update(
    check_only: bool = typer.Option(False, "--check", "-c", help="Check for available updates without applying"),
    force: bool = typer.Option(False, "--force", "-f", help="Force update even if already up to date"),
):
    """
    Self-update Aztec to the latest version from the upstream repository.
    """
    asyncio.run(_update_async(check_only, force))


async def _update_async(check_only: bool, force: bool):
    from aztec_circle.engine.updater import AztecUpdater
    updater = AztecUpdater(console=console)
    if check_only:
        res = updater.check_for_updates()
        if res.has_update:
            console.print(f"[bold yellow]Update available:[/bold yellow] {res.message}")
            console.print("Run [bold cyan]aztec update[/bold cyan] to install.\n")
        else:
            console.print(f"[green]✓ {res.message}[/green] [dim](current: v{res.current_version})[/dim]\n")
        return

    await updater.perform_update(force=force)



def _render_dashboard(state: CircleRunState, last_event: dict) -> Panel:
    table = Table(expand=True, show_header=True, header_style="bold cyan")
    table.add_column("Task ID", style="dim", width=12)
    table.add_column("Phase", style="bold magenta")
    table.add_column("Debate Loop", justify="center")
    table.add_column("Total Spend", justify="right")
    table.add_column("Last Event Payload")

    event_name = last_event.get("event", "IDLE")
    extra = {k: v for k, v in last_event.items() if k not in ("event", "task_id", "cost_usd")}
    detail = f"[bold]{event_name}[/bold] {extra if extra else ''}"

    table.add_row(
        state.task_id[:8],
        state.current_phase.value,
        str(state.loop_count),
        f"${state.total_cost_usd:.4f}",
        detail[:80],
    )
    return Panel(table, title="[bold gold1]Aztec Decision Circle Dashboard[/bold gold1]", border_style="blue")


def slugify_goal(goal: str, max_len: int = 32) -> str:
    """
    Generate clean directory slug from goal prompt.
    """
    stop_words = {
        "a", "an", "the", "create", "build", "make", "design",
        "implement", "write", "develop", "let", "lets", "app",
        "application", "for", "with", "and", "or", "in", "to", "of", "that",
    }
    words = re.sub(r"[^\w\s]", "", goal.lower()).split()
    meaningful = [w for w in words if w not in stop_words]
    if not meaningful:
        meaningful = words[:3]
    slug = "_".join(meaningful[:4])[:max_len].strip("_")
    return slug or "aztec_output"


@app.command()
def run(
    goal: str = typer.Argument(..., help="The goal, prompt, or architectural challenge to resolve"),
    budget: float = typer.Option(1.00, "--budget", "-b", help="Max spend limit in USD"),
    max_loops: int = typer.Option(2, "--max-loops", "-l", help="Max Elder rejection loops"),
    fallback: FallbackPolicy = typer.Option(
        FallbackPolicy.HUMAN_IN_THE_LOOP,
        "--fallback",
        "-f",
        help="Fallback policy upon loop exhaustion",
    ),
    auto_build: bool = typer.Option(
        False,
        "--auto-build",
        "-B",
        help="Automatically scaffold, install dependencies, and build upon resolution",
    ),
    start_server: bool = typer.Option(
        False,
        "--start",
        "-S",
        help="Automatically launch development server after building",
    ),
    port: int = typer.Option(
        5173,
        "--port",
        "-p",
        help="Port for development server",
    ),
    output_dir: Optional[str] = typer.Option(
        None,
        "--output-dir",
        "-o",
        help="Target output directory (defaults to auto-generated slug or ./aztec_output)",
    ),
    max_fix_loops: int = typer.Option(
        2,
        "--max-fix-loops",
        help="Max automated LLM repair iterations on build failure",
    ),
    image: Optional[List[str]] = typer.Option(
        None,
        "--image",
        "-i",
        help="Path or URL to reference image(s) for visual design and specification",
    ),
    paste: bool = typer.Option(
        False,
        "--paste",
        "-P",
        help="Grab and attach image directly from system clipboard",
    ),
    peer_model: Optional[str] = typer.Option(None, "--peer-model", "-m", help="Model for Peer Drafter (Primary)"),
    youth_model: Optional[str] = typer.Option(None, "--youth-model", help="Baseline model for Youth rank"),
    youth_chaos_model: Optional[str] = typer.Option(None, "--youth-chaos-model", help="Model for Youth Chaos Brainstormer"),
    youth_advocate_model: Optional[str] = typer.Option(None, "--youth-advocate-model", help="Model for Youth Devil's Advocate"),
    elder_model: Optional[str] = typer.Option(None, "--elder-model", help="Baseline model for Elder Council"),
    elder_security_model: Optional[str] = typer.Option(None, "--elder-security-model", help="Model for Elder Security Auditor"),
    elder_structural_model: Optional[str] = typer.Option(None, "--elder-structural-model", help="Model for Elder Structural Architect"),
    fallback_model: Optional[str] = typer.Option(None, "--fallback-model", help="Model for Fallback failover"),
):
    """
    Launch a full multi-generational Aztec Circle debate loop.
    """
    all_images = list(image or [])
    if paste:
        from aztec_circle.adapters.clipboard_utils import get_clipboard_image
        clip_img = get_clipboard_image()
        if clip_img:
            all_images.append(clip_img)
            console.print(f"  [green]📷 Attached image from clipboard:[/green] [dim]{clip_img}[/dim]")
        else:
            console.print("  [yellow]Warning: No image found in system clipboard.[/yellow]")

    console.print(f"[bold cyan]Initializing Aztec Circle for task:[/bold cyan] {goal}")
    if all_images:
        console.print(f"  [dim]Attached {len(all_images)} reference image(s)[/dim]")
    asyncio.run(_run_async(
        goal, budget, max_loops, fallback, auto_build, start_server, port, output_dir, max_fix_loops, all_images,
        peer_model=peer_model,
        youth_model=youth_model,
        youth_chaos_model=youth_chaos_model,
        youth_advocate_model=youth_advocate_model,
        elder_model=elder_model,
        elder_security_model=elder_security_model,
        elder_structural_model=elder_structural_model,
        fallback_model=fallback_model,
    ))


async def _run_async(
    goal: str,
    budget: float,
    max_loops: int,
    fallback: FallbackPolicy,
    auto_build: bool = False,
    start_server: bool = False,
    port: int = 5173,
    output_dir: Optional[str] = None,
    max_fix_loops: int = 2,
    images: Optional[List[str]] = None,
    peer_model: Optional[str] = None,
    youth_model: Optional[str] = None,
    youth_chaos_model: Optional[str] = None,
    youth_advocate_model: Optional[str] = None,
    elder_model: Optional[str] = None,
    elder_security_model: Optional[str] = None,
    elder_structural_model: Optional[str] = None,
    fallback_model: Optional[str] = None,
):
    from aztec_circle.adapters.image_utils import parse_images_input
    from aztec_circle.config import settings

    if peer_model:
        settings.PEER_MODEL = peer_model
    if youth_model:
        settings.YOUTH_MODEL = youth_model
    if youth_chaos_model:
        settings.YOUTH_CHAOS_MODEL = youth_chaos_model
    if youth_advocate_model:
        settings.YOUTH_ADVOCATE_MODEL = youth_advocate_model
    if elder_model:
        settings.ELDER_MODEL = elder_model
    if elder_security_model:
        settings.ELDER_SECURITY_MODEL = elder_security_model
    if elder_structural_model:
        settings.ELDER_STRUCTURAL_MODEL = elder_structural_model
    if fallback_model:
        settings.FALLBACK_MODEL = fallback_model

    parsed_images = parse_images_input(images)
    state = CircleRunState(
        goal=goal,
        images=parsed_images,
        budget_limit_usd=budget,
        max_loops=max_loops,
        fallback_policy=fallback,
    )
    event_queue: asyncio.Queue = asyncio.Queue()
    last_event: dict = {"event": "INITIALIZING"}

    orchestrator = AztecOrchestrator(state=state, event_queue=event_queue)

    with Live(_render_dashboard(state, last_event), console=console, refresh_per_second=4) as live:
        async def _event_consumer():
            nonlocal last_event
            while True:
                try:
                    event = await event_queue.get()
                    last_event = event
                    live.update(_render_dashboard(state, last_event))
                    event_queue.task_done()
                except asyncio.CancelledError:
                    break

        consumer_task = asyncio.create_task(_event_consumer())

        try:
            result = await orchestrator.run()
            consumer_task.cancel()
            live.update(_render_dashboard(state, {"event": "COMPLETED"}))
            console.print("\n[bold green]=== Aztec Circle Execution Final Result ===[/bold green]")
            console.print_json(data=result)

            target_out = output_dir or f"./{slugify_goal(goal)}"
            from aztec_circle.tui.renderer import TranscriptRenderer
            renderer = TranscriptRenderer(console)
            renderer.render_deliverable(result, output_dir=target_out)

            if auto_build or start_server:
                from aztec_circle.engine.scaffolder import find_project_root
                from aztec_circle.engine.project_runner import ProjectRunner
                from aztec_circle.engine.build_fixer import BuildFixAgent

                project_root = find_project_root(target_out)
                console.print(f"\n[bold cyan]─── Auto-Building Deliverable Project ({project_root}) ───[/bold cyan]")
                runner = ProjectRunner(console=console)
                install_res = await runner.install_dependencies(project_root)
                if install_res.success:
                    build_res = await runner.build_project(project_root)
                    if not build_res.success and max_fix_loops > 0:
                        fixer = BuildFixAgent(console=console, max_iterations=max_fix_loops)
                        fix_res = await fixer.fix(project_root, build_res, runner=runner)
                        build_res = fix_res.final_build_result

                    if build_res.success and start_server:
                        server_proc = await runner.start_dev_server(project_root, port=port)
                        console.print("[dim]Press Ctrl+C to stop dev server...[/dim]")
                        try:
                            await server_proc.process.wait()
                        except (KeyboardInterrupt, asyncio.CancelledError):
                            await server_proc.stop()
                            console.print("[yellow]Dev server stopped.[/yellow]")

        except Exception as exc:
            consumer_task.cancel()
            live.update(_render_dashboard(state, {"event": "ERROR", "error": str(exc)}))
            console.print(f"\n[bold red]Circle Execution Terminated:[/bold red] {exc}")
        finally:
            # Yield brief interval for underlying SSL sockets / transports to close gracefully
            await asyncio.sleep(0.05)


@app.command()
def build(
    path: str = typer.Argument("./aztec_output", help="Project directory to scaffold and build"),
    max_fix_loops: int = typer.Option(2, "--max-fix-loops", help="Max automated LLM repair attempts if build fails"),
):
    """
    Scaffold missing project configuration, install dependencies, and build project.
    """
    asyncio.run(_build_async(path, max_fix_loops))


async def _build_async(path: str, max_fix_loops: int = 2):
    from aztec_circle.engine.scaffolder import scaffold_project
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent

    console.print(f"[bold cyan]Scaffolding and building project at:[/bold cyan] {path}")
    scaffold_res = scaffold_project(path)
    if scaffold_res.files_injected:
        console.print(f"  [green]✓[/green] Injected {len(scaffold_res.files_injected)} boilerplate configuration files: [dim]{', '.join(scaffold_res.files_injected)}[/dim]")

    runner = ProjectRunner(console=console)
    install_res = await runner.install_dependencies(scaffold_res.project_root)
    if install_res.success:
        build_res = await runner.build_project(scaffold_res.project_root)
        if not build_res.success and max_fix_loops > 0:
            fixer = BuildFixAgent(console=console, max_iterations=max_fix_loops)
            await fixer.fix(scaffold_res.project_root, build_res, runner=runner)


@app.command()
def edit(
    instruction: str = typer.Argument(..., help="Edit instruction (e.g. 'Add a screenshot button to the Toolbar')"),
    path: str = typer.Option("./aztec_output", "--path", "-p", help="Target project directory to edit"),
    auto_typecheck: bool = typer.Option(True, "--typecheck/--no-typecheck", help="Run tsc check after editing"),
    auto_fix: bool = typer.Option(True, "--fix/--no-fix", help="Automatically invoke BuildFixAgent if typecheck fails"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Display token telemetry and detailed patch operations"),
    image: Optional[List[str]] = typer.Option(
        None,
        "--image",
        "-i",
        help="Path or URL to reference image(s) for visual edit guidance",
    ),
    paste: bool = typer.Option(
        False,
        "--paste",
        "-P",
        help="Grab and attach image directly from system clipboard",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        "--auto-approve",
        help="Automatically approve and execute proposed console/database commands without prompt",
    ),
):
    """
    Apply an atomic targeted edit to an existing generated project with optional image references.
    Uses a 2-round LLM conversation for maximum token efficiency.
    """
    all_images = list(image or [])
    if paste:
        from aztec_circle.adapters.clipboard_utils import get_clipboard_image
        clip_img = get_clipboard_image()
        if clip_img:
            all_images.append(clip_img)
            console.print(f"  [green]📷 Attached image from clipboard:[/green] [dim]{clip_img}[/dim]")
        else:
            console.print("  [yellow]Warning: No image found in system clipboard.[/yellow]")

    asyncio.run(_edit_async(instruction, path, auto_typecheck, auto_fix, verbose, all_images, yes))


async def _edit_async(
    instruction: str,
    path: str,
    auto_typecheck: bool,
    auto_fix: bool,
    verbose: bool,
    images: Optional[List[str]] = None,
    auto_approve_commands: bool = False,
):
    from aztec_circle.adapters.image_utils import parse_images_input
    from aztec_circle.engine.patch_agent import PatchAgent
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent
    from aztec_circle.engine.scaffolder import find_project_root
    from aztec_circle.tui.interactive import prompt_confirm_console_command

    parsed_images = parse_images_input(images)
    root = find_project_root(path)

    async def _confirm_cb(cmd_obj):
        return await prompt_confirm_console_command(cmd_obj, console, root)

    agent = PatchAgent(console=console)
    res = await agent.run(
        instruction=instruction,
        project_dir=root,
        images=parsed_images,
        verbose=verbose,
        confirm_command_callback=_confirm_cb if not auto_approve_commands else None,
        auto_approve_commands=auto_approve_commands,
    )

    if not res.success:
        console.print(f"[bold red]✗ Edit operation failed:[/bold red] {res.error_message or res.edit_summary}\n")
        return

    console.print(f"\n[bold green]Summary:[/bold green] {res.edit_summary}")

    if auto_typecheck:
        runner = ProjectRunner(console=console)
        tc_res = await runner.typecheck_project(root)
        if not tc_res.success:
            if auto_fix:
                console.print("[yellow]Type check reported errors. Triggering atomic Build Fix Agent...[/yellow]")
                fixer = BuildFixAgent(console=console, max_iterations=2)
                fix_res = await fixer.fix(root, tc_res, runner=runner)
                if not fix_res.success:
                    console.print("[bold red]Warning: Post-edit build check still has unresolved errors.[/bold red]\n")
            else:
                console.print("[bold red]Type check failed.[/bold red]\n")
        else:
            console.print("[bold green]✓ Type check passed with zero errors![/bold green]\n")


@app.command()
def fix(
    path: str = typer.Argument("./aztec_output", help="Project directory to repair"),
    max_loops: int = typer.Option(3, "--max-loops", "-n", help="Max automated LLM repair iterations"),
):
    """
    Run the Build Fix Agent on a project: automatically patch compiler errors and rebuild.
    """
    asyncio.run(_fix_async(path, max_loops))


async def _fix_async(path: str, max_loops: int):
    from aztec_circle.engine.scaffolder import find_project_root
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent

    root = find_project_root(path)
    console.print(f"[bold cyan]Running Aztec Build Fixer on project at:[/bold cyan] {root}")
    runner = ProjectRunner(console=console)
    initial_build = await runner.build_project(root)

    if initial_build.success:
        console.print("[bold green]✓ Project is already building cleanly with zero errors![/bold green]")
        return

    fixer = BuildFixAgent(console=console, max_iterations=max_loops)
    res = await fixer.fix(root, initial_build, runner=runner)
    if res.success:
        console.print(f"[bold green]✓ Successfully repaired {len(res.patches_applied)} file(s) across {res.iterations} iteration(s)![/bold green]")
    else:
        console.print(f"[bold red]✗ Could not fully resolve all build errors after {res.iterations} iteration(s).[/bold red]")


@app.command()
def test(
    path: str = typer.Argument("./aztec_output", help="Project directory to test"),
):
    """
    Execute project test suite (npm test or pytest).
    """
    asyncio.run(_test_async(path))


async def _test_async(path: str):
    from aztec_circle.engine.scaffolder import find_project_root
    from aztec_circle.engine.project_runner import ProjectRunner

    root = find_project_root(path)
    console.print(f"[bold cyan]Running test suite for project at:[/bold cyan] {root}")
    runner = ProjectRunner(console=console)
    await runner.test_project(root)


@app.command()
def start(
    path: str = typer.Argument(None, help="Project directory to run (positional)"),
    path_opt: str = typer.Option(None, "--path", help="Project directory to run (optional flag)"),
    port: int = typer.Option(5173, "--port", help="Port to bind development server"),
):
    """
    Build and launch the live development server for the generated project.
    """
    target_path = path_opt or path or "./aztec_output"
    asyncio.run(_start_async(target_path, port))


async def _start_async(path: str, port: int):
    from aztec_circle.engine.scaffolder import scaffold_project
    from aztec_circle.engine.project_runner import ProjectRunner

    scaffold_res = scaffold_project(path)
    runner = ProjectRunner(console=console)

    # Ensure dependencies and build are ready
    install_res = await runner.install_dependencies(scaffold_res.project_root)
    if not install_res.success:
        console.print("[bold red]Dependency installation failed. Aborting dev server start.[/bold red]")
        return

    server_proc = await runner.start_dev_server(scaffold_res.project_root, port=port)
    console.print("[dim]Dev server running in foreground. Press Ctrl+C to stop.[/dim]")
    try:
        await server_proc.process.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        await server_proc.stop()
        console.print("\n[yellow]Dev server stopped cleanly.[/yellow]")


@app.command()
def resume(
    task_id: str = typer.Argument(..., help="Task ID of previous checkpoint to resume"),
):
    """
    Resume an existing run from SQLite checkpoint.
    """
    asyncio.run(_resume_async(task_id))


async def _resume_async(task_id: str):
    store = CheckpointStore()
    state = await store.load(task_id)
    if not state:
        console.print(f"[bold red]Error: No checkpoint found for task ID: {task_id}[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Resuming task {task_id} from phase {state.current_phase.value}[/bold green]")
    event_queue: asyncio.Queue = asyncio.Queue()
    orchestrator = AztecOrchestrator(state=state, event_queue=event_queue, checkpoint_store=store)

    try:
        result = await orchestrator.run()
        console.print("\n[bold green]=== Resumed Run Result ===[/bold green]")
        console.print_json(data=result)
    except Exception as exc:
        console.print(f"[bold red]Resumed run failed:[/bold red] {exc}")


@app.command("list-runs")
def list_runs():
    """
    List historical task runs stored in SQLite.
    """
    asyncio.run(_list_runs_async())


@app.command("runs")
def runs_alias():
    """
    Alias for list-runs: show historical task runs.
    """
    asyncio.run(_list_runs_async())


@app.command("help")
def help_command(ctx: typer.Context):
    """
    Show the Aztec CLI help overview.
    """
    parent = ctx.parent or ctx
    console.print(parent.get_help())


@app.command()
def stop(
    ports: bool = typer.Option(True, "--ports", "-p", help="Free standard development server port ranges"),
):
    """
    Stop background development servers started by Aztec (frees dev ports).
    """
    from aztec_circle.engine.project_runner import free_ports

    target_ports = list(range(5173, 5186)) + list(range(8000, 8016))
    freed = free_ports(target_ports) if ports else []
    if freed:
        console.print(
            f"[bold green]✓ Stopped background servers on ports:[/bold green] {', '.join(str(p) for p in freed)}"
        )
    else:
        console.print("[dim]No background development servers running.[/dim]")


# ── Tool subsystem ───────────────────────────────────────────────────────────

tool_app = typer.Typer(help="Inspect, run, and create safe project tools.")
app.add_typer(tool_app, name="tool")


def _tool_args_from_pairs(pairs: List[str]) -> dict:
    args: dict = {}
    for pair in pairs:
        if "=" not in pair:
            raise typer.BadParameter(f"expected key=value, got '{pair}'")
        k, v = pair.split("=", 1)
        args[k] = v
    return args


@tool_app.command("list")
def tool_list_cmd(
    path: str = typer.Option(".", "--path", "-p", help="Project root"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show parameters and templates"),
):
    """List available tools (built-in + project + global custom tools)."""
    from aztec_circle.tools import get_registry
    from rich.table import Table as RichTable

    reg = get_registry(path)
    table = RichTable(title=f"Aztec Tools ({path})", header_style="bold cyan", expand=True)
    table.add_column("Tool", style="bold white")
    table.add_column("Safety", style="magenta", width=10)
    table.add_column("Source", style="dim", width=8)
    if verbose:
        table.add_column("Params / Template", style="green", overflow="fold")
    for spec in reg.list():
        safety_style = {"read_only": "green", "mutating": "yellow", "dangerous": "bold red"}.get(spec.safety.value, "white")
        row = [spec.name, f"[{safety_style}]{spec.safety.value}[/{safety_style}]", reg.source_of(spec.name)]
        if verbose:
            detail = spec.template or ", ".join(spec.params) or "—"
            row.append(detail)
        table.add_row(*row)
    console.print(table)
    console.print("[dim]Run: aztec tool run <name> key=value …  ·  Create: aztec tool create --help[/dim]\n")


@tool_app.command("run")
def tool_run_cmd(
    name: str = typer.Argument(..., help="Tool name"),
    args: Optional[List[str]] = typer.Argument(None, help="Arguments as key=value pairs"),
    path: str = typer.Option(".", "--path", "-p", help="Project root"),
    json_args: Optional[str] = typer.Option(None, "--json", help="Arguments as JSON object"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Auto-approve confirmation gates"),
):
    """Execute a tool against the project."""
    import asyncio

    from aztec_circle.tools import ToolContext, get_registry

    raw: dict = {}
    if json_args:
        try:
            parsed = __import__("json").loads(json_args)
            if not isinstance(parsed, dict):
                raise ValueError("--json must be an object")
            raw.update(parsed)
        except (ValueError, __import__("json").JSONDecodeError) as exc:
            console.print(f"[bold red]Invalid --json:[/bold red] {exc}")
            raise typer.Exit(code=1)
    raw.update(_tool_args_from_pairs(list(args or [])))

    registry = get_registry(path)
    ctx = ToolContext(project_root=path, auto_approve=yes)

    async def _go():
        return await registry.execute(name, raw, ctx)

    result = asyncio.run(_go())
    if result.output:
        console.print(result.output.rstrip())
    if not result.ok:
        console.print(f"[bold red]✗ {name} failed[/bold red]"
                      + (f": {result.error}" if result.error else "")
                      + f" [dim](exit={result.exit_code}, {result.duration_ms}ms)[/dim]")
        raise typer.Exit(code=1)
    console.print(f"[dim]{name} ok · exit=0 · {result.duration_ms}ms[/dim]")


@tool_app.command("create")
def tool_create_cmd(
    name: str = typer.Argument(..., help="Tool name (lowercase_snake)"),
    template: str = typer.Option(..., "--template", "-t", help='Shell command with {placeholders}, e.g. "wc -l {file}"'),
    description: str = typer.Option("", "--desc", "-d"),
    safety: str = typer.Option("mutating", "--safety", help="read_only | mutating | dangerous"),
    scope: str = typer.Option("project", "--scope", help="project (.aztec/tools) or global (~/.aztec/tools.d)"),
    param: Optional[List[str]] = typer.Option(None, "--param", help="Param spec 'name:type[:regex]' (repeatable)"),
    timeout: float = typer.Option(60.0, "--timeout", help="Timeout seconds"),
    path: str = typer.Option(".", "--path", "-p", help="Project root"),
):
    """Create a persistent custom shell-template tool."""
    from aztec_circle.tools import ParamSpec, ParamType, SafetyClass, ToolSpec
    from aztec_circle.tools.registry import ToolRegistry

    params: dict = {}
    for p in param or []:
        parts = p.split(":", 2)
        pname = parts[0]
        ptype = ParamType(parts[1]) if len(parts) > 1 and parts[1] in ("str", "int", "float", "bool") else ParamType.STR
        pattern = parts[2] if len(parts) > 2 else None
        params[pname] = ParamSpec(name=pname, type=ptype, pattern=pattern)

    spec = ToolSpec(
        name=name,
        description=description or f"custom tool {name}",
        safety=SafetyClass(safety),
        params=params,
        template=template,
        timeout_s=timeout,
    )
    registry = ToolRegistry(project_root=path)
    saved = registry.save_tool(spec, scope=scope)
    console.print(f"[bold green]✓ Tool '{name}' created:[/bold green] {saved}")
    console.print(f"[dim]Try it: aztec tool run {name} … --yes[/dim]")


@tool_app.command("remove")
def tool_remove_cmd(
    name: str = typer.Argument(...),
    scope: Optional[str] = typer.Option(None, "--scope", help="project | global (default: both)"),
    path: str = typer.Option(".", "--path", "-p"),
):
    """Remove a saved custom tool."""
    from aztec_circle.tools.registry import ToolRegistry

    removed = ToolRegistry(project_root=path).remove_tool(name, scope=scope)
    if removed:
        console.print(f"[bold green]✓ Removed '{name}'.[/bold green]")
    else:
        console.print(f"[yellow]'{name}' was not a saved custom tool.[/yellow]")
        raise typer.Exit(code=1)


async def _list_runs_async():
    store = CheckpointStore()
    runs = await store.list_runs()
    if not runs:
        console.print("[dim]No runs found in checkpoint database.[/dim]")
        return

    table = Table(title="Aztec Circle Checkpointed Runs", show_header=True, header_style="bold cyan")
    table.add_column("Task ID", style="dim")
    table.add_column("Phase", style="bold magenta")
    table.add_column("Loops", justify="center")
    table.add_column("Cost ($)", justify="right")
    table.add_column("Updated At")
    table.add_column("Goal")

    for r in runs:
        table.add_row(
            str(r.get("task_id", ""))[:8],
            str(r.get("phase", "")),
            str(r.get("loops", 0)),
            f"${float(r.get('cost_usd', 0.0)):.4f}",
            str(r.get("updated_at", ""))[:19],
            str(r.get("goal", ""))[:40],
        )

    console.print(table)


@app.command()
def config(
    set_key: Optional[str] = typer.Option(None, "--set-key", "-k", help="Set an API key (e.g. GEMINI_API_KEY=AIzaSy...)"),
    set_model: Optional[str] = typer.Option(None, "--set-model", "-m", help="Set a rank model (e.g. YOUTH=gemini/gemini-3.7-flash)"),
    preset: Optional[str] = typer.Option(None, "--preset", "-P", help="Apply an architecture preset (e.g. max_reasoning, speed_budget)"),
    test: bool = typer.Option(False, "--test", "-t", help="Probe active rank models with a live latency ping test"),
    list_models: bool = typer.Option(False, "--list-models", "-l", help="List curated models across all supported providers"),
):
    """
    Manage API keys, model assignments, presets, and connection tests.
    """
    from aztec_circle.engine.config_manager import ConfigManager
    from aztec_circle.tui.config_ui import (
        render_api_keys_table,
        render_ranks_table,
        render_presets_table,
        render_model_catalog_table,
        run_test_models,
        run_interactive_config_menu,
    )
    from aztec_circle.tui.session import SessionState

    if set_key:
        if "=" in set_key:
            k, v = set_key.split("=", 1)
            ConfigManager.save_api_key(k, v)
            console.print(f"[bold green]✓ Successfully updated and secured {k} in ~/.aztec/config.env[/bold green]\n")
        else:
            console.print("[bold red]Invalid format for --set-key. Use KEY_NAME=VALUE[/bold red]\n")
        return

    if set_model:
        if "=" in set_model:
            rank, model_id = set_model.split("=", 1)
            ConfigManager.save_model_assignment(rank, model_id)
            console.print(f"[bold green]✓ Assigned {rank.upper()} to {model_id}[/bold green]\n")
        else:
            console.print("[bold red]Invalid format for --set-model. Use RANK=MODEL_ID[/bold red]\n")
        return

    if preset:
        if ConfigManager.apply_preset(preset):
            console.print(f"[bold green]✓ Successfully applied preset '{preset}'[/bold green]\n")
        else:
            console.print(f"[bold red]Unknown preset '{preset}'.[/bold red]\n")
            render_presets_table(console)
        return

    if list_models:
        render_model_catalog_table(console)
        return

    if test:
        asyncio.run(run_test_models(console))
        return

    # Default action: render current configuration overview
    render_api_keys_table(console)
    render_ranks_table(console)


@app.command()
def plan(
    path: str = typer.Argument("./aztec_output", help="Project directory containing or to receive AZTEC_PLAN.md"),
    sync: bool = typer.Option(False, "--sync", "-s", help="Scan codebase files and synchronize AZTEC_PLAN.md"),
    file_only: bool = typer.Option(False, "--file", "-f", help="Output only the absolute path to AZTEC_PLAN.md"),
):
    """
    Display or synchronize the living project blueprint and roadmap (AZTEC_PLAN.md).
    """
    from aztec_circle.engine.plan_manager import PlanManager

    if sync:
        p = PlanManager.sync_from_codebase(path)
        console.print(f"[bold green]✓ Synchronized Living Blueprint:[/bold green] [underline]{p}[/underline]\n")
        PlanManager.render_plan_dashboard(path, console)
    elif file_only:
        p = PlanManager.get_plan_path(path)
        console.print(str(p))
    else:
        PlanManager.render_plan_dashboard(path, console)


@app.command("clean")
def clean(
    path: str = typer.Argument(None, help="Project directory to clean (optional)"),
    ports: bool = typer.Option(True, "--ports", "-p", help="Free occupied development server ports (5173-5185, 8000-8015)"),
):
    """
    Clean up temporary artifacts and free lingering background server ports.
    """
    from aztec_circle.engine.project_runner import free_ports
    if ports:
        target_ports = list(range(5173, 5186)) + list(range(8000, 8016))
        freed = free_ports(target_ports)
        if freed:
            console.print(f"[bold green]✓ Freed occupied server ports:[/bold green] {', '.join(str(p) for p in freed)}")
        else:
            console.print("[dim]No lingering server processes found on development ports (5173–5185, 8000–8015).[/dim]")
    console.print("[bold green]✓ Aztec workspace cleanup complete.[/bold green]")


@app.command()
def serve(
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind Web Inspector"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host address to bind"),
):
    """
    Start the FastAPI & WebSocket real-time Web Inspector server.
    """
    import uvicorn
    from aztec_circle.server.app import create_app

    console.print(f"[bold green]Starting Aztec Web Inspector at http://{host}:{port}[/bold green]")
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    app()


