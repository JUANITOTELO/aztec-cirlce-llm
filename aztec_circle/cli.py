"""
CLI entry point for Aztec Decision Circle.
"""

from __future__ import annotations

import asyncio
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
    no_args_is_help=True,
)
console = Console()


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
):
    """
    Launch a full multi-generational Aztec Circle debate loop.
    """
    console.print(f"[bold cyan]Initializing Aztec Circle for task:[/bold cyan] {goal}")
    asyncio.run(_run_async(goal, budget, max_loops, fallback))


async def _run_async(goal: str, budget: float, max_loops: int, fallback: FallbackPolicy):
    state = CircleRunState(
        goal=goal,
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
        except Exception as exc:
            consumer_task.cancel()
            live.update(_render_dashboard(state, {"event": "ERROR", "error": str(exc)}))
            console.print(f"\n[bold red]Circle Execution Terminated:[/bold red] {exc}")


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
