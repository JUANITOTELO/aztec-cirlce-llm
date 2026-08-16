"""
Interactive agy-style REPL session for Aztec Decision Circle.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.live import Live

from aztec_circle.domain.models import CircleRunState
from aztec_circle.engine.checkpoint import CheckpointStore
from aztec_circle.engine.state_machine import AztecOrchestrator
from aztec_circle.tui.commands import dispatch_slash_command
from aztec_circle.tui.completer import SlashCompleter
from aztec_circle.tui.renderer import TranscriptRenderer, print_welcome_banner
from aztec_circle.tui.session import SessionState

console = Console()

TUI_STYLE = Style.from_dict({
    "prompt": "ansicyan bold",
    "completion-menu.completion": "bg:#202020 #ffffff",
    "completion-menu.completion.current": "bg:#00aaaa #000000 bold",
    "completion-menu.meta.completion": "bg:#101010 #aaaaaa italic",
})


async def run_debate_session(
    goal: str,
    state: SessionState,
    renderer: TranscriptRenderer,
) -> Optional[dict]:
    """Execute a full Aztec Decision Circle debate within the interactive session."""
    run_state = CircleRunState(
        goal=goal,
        images=list(state.attached_images),
        budget_limit_usd=state.budget_limit_usd,
        max_loops=state.max_loops,
        fallback_policy=state.fallback_policy,
    )
    event_queue: asyncio.Queue = asyncio.Queue()
    orchestrator = AztecOrchestrator(state=run_state, event_queue=event_queue, console=console)

    console.print(f"\n[bold cyan]Starting Aztec Debate for:[/bold cyan] {goal}")
    if state.attached_images:
        console.print(f"  [dim]Including {len(state.attached_images)} reference image(s)[/dim]")
    renderer.render_phase("YOUTH_BRAINSTORM")

    # Background event consumer to render events live
    async def _event_drainer():
        while True:
            try:
                event = await event_queue.get()
                renderer.render_event(event)
                event_queue.task_done()
            except asyncio.CancelledError:
                break

    drain_task = asyncio.create_task(_event_drainer())

    try:
        result = await orchestrator.run()
        await asyncio.sleep(0.05)  # flush pending events
        drain_task.cancel()

        # Update session telemetry
        state.last_goal = goal
        cost = result.get("total_cost_usd", run_state.total_cost_usd)
        tokens = result.get("total_tokens_used", run_state.total_tokens_used)
        loops = result.get("loop_count", run_state.loop_count)
        task_id = result.get("task_id", run_state.task_id)
        state.record_run(cost_usd=cost, tokens=tokens, loops=loops, task_id=task_id)

        # Render deliverable
        renderer.render_deliverable(result, output_dir=state.output_dir)
        await _show_post_debate_menu(state, console)
        return result

    except asyncio.CancelledError:
        drain_task.cancel()
        console.print("\n[yellow]Debate cancelled by user.[/yellow]\n")
        return None
    except Exception as exc:
        drain_task.cancel()
        console.print(f"\n[bold red]Debate execution encountered an error:[/bold red] {exc}\n")
        return None


def _is_edit_followup(goal: str, state: SessionState) -> bool:
    """
    Determine whether input is an incremental follow-up edit to the active project.
    Heuristics:
    - Edit mode is enabled
    - Project output_dir exists and contains source files in src/
    - Input does NOT start with major project generation trigger keywords
    """
    import os
    import re
    if not state.edit_mode_enabled:
        return False

    src_dir = os.path.join(state.output_dir, "src")
    if not (os.path.isdir(src_dir) and any(f.endswith((".ts", ".tsx", ".js", ".jsx", ".py")) for f in os.listdir(src_dir))):
        return False

    words = re.sub(r"[^\w\s]", "", goal.strip().lower()).split()
    if not words:
        return False

    trigger_words = {
        "create", "build", "design", "make", "generate",
        "develop", "write", "initialize", "start", "let", "lets",
    }
    return words[0] not in trigger_words


def _is_modular_consensus_request(goal: str, state: SessionState) -> bool:
    """Check if goal is requesting a new module, major architectural feature, or consensus on existing project."""
    import os
    src_dir = os.path.join(state.output_dir, "src")
    if not (os.path.isdir(src_dir) and any(f.endswith((".ts", ".tsx", ".js", ".jsx", ".py")) for f in os.listdir(src_dir))):
        return False

    g_lower = goal.strip().lower()
    module_triggers = [
        "new module", "create module", "add module", "build module",
        "create a module", "add a module", "build a module",
        "new feature", "implement module", "module for",
        "consensus", "architect a module", "architect module",
        "production ready module", "holistic",
    ]
    return any(t in g_lower for t in module_triggers)


async def run_modular_consensus_session(
    goal: str,
    state: SessionState,
    console: Console,
) -> Optional[Any]:
    """Execute a modular edit consensus debate to architect and build a new module into the active project."""
    import os
    from aztec_circle.engine.modular_consensus import ModularConsensusOrchestrator
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent
    from aztec_circle.engine.scaffolder import find_project_root

    target_dir = state.output_dir
    if not os.path.exists(target_dir) or target_dir == "./aztec_output":
        if os.path.exists("package.json") or os.path.exists("src"):
            target_dir = "."

    root = find_project_root(target_dir)
    console.print(f"\n[bold cyan]🏛  Aztec Modular Consensus Engine[/bold cyan] [dim](target: {root})[/dim]")
    console.print(f"[bold]Architecting Module / Feature:[/bold] {goal}\n")

    async def _confirm_cb(cmd_obj: Any) -> Tuple[bool, Optional[str]]:
        return await prompt_confirm_console_command(cmd_obj, console, root)

    orchestrator = ModularConsensusOrchestrator(
        project_dir=root,
        goal=goal,
        images=list(state.attached_images),
        console=console,
        budget_limit_usd=state.budget_limit_usd,
        max_loops=state.max_loops,
    )

    try:
        res = await orchestrator.run(
            confirm_command_callback=_confirm_cb,
            auto_approve_commands=False,
            verbose=True,
        )

        if not res.success:
            console.print(f"[bold red]✗ Modular Consensus failed:[/bold red] {res.error_message}\n")
            return None

        state.record_cost(res.total_cost_usd, res.total_tokens_used)

        # Quality Gate: Type Check + Test Suite
        runner = ProjectRunner(console=console)
        tc_res = await runner.typecheck_project(root)
        gate_failed = not tc_res.success

        if gate_failed:
            console.print("[yellow]Type check found compiler errors. Triggering atomic Build Fix Agent...[/yellow]")
            fixer = BuildFixAgent(console=console, max_iterations=2)
            fix_res = await fixer.fix(root, tc_res, runner=runner)
            state.record_cost(fix_res.total_cost_usd)
            if not fix_res.success:
                console.print("[bold red]Warning: Unresolved type errors remain.[/bold red]\n")
                gate_failed = True
            else:
                gate_failed = False

        # Run tests if a test script exists in package.json and type check is clean
        pkg_json_path = os.path.join(root, "package.json")
        has_test_script = False
        if os.path.exists(pkg_json_path):
            try:
                import json as _json
                with open(pkg_json_path, "r", encoding="utf-8") as _f:
                    _pkg = _json.load(_f)
                has_test_script = "test" in _pkg.get("scripts", {})
            except Exception:
                pass

        if not gate_failed and has_test_script:
            console.print("[dim]Running test suite as secondary quality gate...[/dim]")
            test_res = await runner.run_shell_command_streamed(
                cmd_str="npm run test -- --run",
                cwd=root,
                title="Quality Gate: Test Suite",
            )
            if not test_res.success:
                console.print("[yellow]Tests failed. Triggering Build Fix Agent on test errors...[/yellow]")
                fixer = BuildFixAgent(console=console, max_iterations=2)
                fix_res = await fixer.fix(root, test_res, runner=runner)
                state.record_cost(fix_res.total_cost_usd)
                if not fix_res.success:
                    console.print("[bold red]Warning: Unresolved test failures remain.[/bold red]\n")
                else:
                    console.print("[bold green]✓ Quality gate passed: tests healed cleanly![/bold green]\n")
            else:
                console.print("[bold green]✓ Quality gate passed: type check + tests clean![/bold green]\n")
        elif not gate_failed:
            console.print("[bold green]✓ Quality gate passed: type check clean![/bold green]\n")

        await _show_post_debate_menu(state, console)
        return res

    except Exception as exc:
        console.print(f"[bold red]Modular Consensus encountered an error:[/bold red] {exc}\n")
        return None


async def prompt_confirm_console_command(
    cmd_obj: Any,
    console: Console,
    project_root: str,
) -> Tuple[bool, Optional[str]]:
    """Interactive confirmation prompt for a proposed console command."""
    from rich.panel import Panel
    from rich.table import Table
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import ANSI

    table = Table(box=None, show_header=False, padding=(0, 1))
    table.add_column("Field", style="bold cyan", width=14)
    table.add_column("Value", style="white")

    table.add_row("Command:", f"[bold yellow]{cmd_obj.command}[/bold yellow]")
    table.add_row("Purpose:", f"[white]{cmd_obj.description}[/white]")
    table.add_row("Stage:", f"[magenta]{cmd_obj.stage}[/magenta]")
    table.add_row("Directory:", f"[dim]{cmd_obj.cwd or project_root}[/dim]")

    console.print()
    console.print(Panel(table, title="[bold yellow]⚡ Proposed Console Command[/bold yellow]", border_style="yellow"))

    prompt_session: PromptSession = PromptSession()
    try:
        ans = await prompt_session.prompt_async(
            ANSI("\x1b[1;36mExecute this command? [\x1b[1;32mY\x1b[0;36mes / \x1b[1;31mn\x1b[0;36mo / \x1b[1;33me\x1b[0;36mdit]: \x1b[0m")
        )
        ans_clean = ans.strip().lower()
        if ans_clean in ("", "y", "yes"):
            return True, None
        elif ans_clean in ("n", "no"):
            return False, None
        elif ans_clean in ("e", "edit"):
            edit_prompt: PromptSession = PromptSession()
            edited = await edit_prompt.prompt_async(
                ANSI("\x1b[1;33mEdit command: \x1b[0m"),
                default=cmd_obj.command,
            )
            return True, edited.strip() if edited.strip() else cmd_obj.command
        else:
            return True, None
    except (EOFError, KeyboardInterrupt):
        return False, None


async def run_edit_session(
    instruction: str,
    state: SessionState,
    console: Console,
) -> None:
    """Apply an atomic incremental edit within the interactive session."""
    import os
    from aztec_circle.engine.patch_agent import PatchAgent
    from aztec_circle.engine.project_runner import ProjectRunner
    from aztec_circle.engine.build_fixer import BuildFixAgent
    from aztec_circle.engine.scaffolder import find_project_root

    target_dir = state.output_dir
    if not os.path.exists(target_dir) or target_dir == "./aztec_output":
        if os.path.exists("package.json") or os.path.exists("src"):
            target_dir = "."

    root = find_project_root(target_dir)
    console.print(f"\n[bold cyan]✏ Edit Mode Detected[/bold cyan] [dim](target: {root})[/dim]")
    console.print("[dim]Applying atomic line-range patch. Type /rebuild to force full regeneration.[/dim]")

    async def _confirm_cb(cmd_obj: Any) -> Tuple[bool, Optional[str]]:
        return await prompt_confirm_console_command(cmd_obj, console, root)

    agent = PatchAgent(console=console)
    res = await agent.run(
        instruction=instruction,
        project_dir=root,
        images=list(state.attached_images),
        verbose=True,
        confirm_command_callback=_confirm_cb,
    )

    if not res.success:
        console.print(f"[bold red]✗ Edit failed:[/bold red] {res.error_message or res.edit_summary}\n")
        return

    state.record_cost(res.total_cost_usd, res.round1_tokens + res.round2_tokens)
    console.print(f"[bold green]Summary:[/bold green] {res.edit_summary}")

    # Quality Gate check
    runner = ProjectRunner(console=console)
    tc_res = await runner.typecheck_project(root)
    if not tc_res.success:
        console.print("[yellow]Type check found errors. Triggering atomic Build Fix Agent...[/yellow]")
        fixer = BuildFixAgent(console=console, max_iterations=2)
        fix_res = await fixer.fix(root, tc_res, runner=runner)
        state.record_cost(fix_res.total_cost_usd)
        if not fix_res.success:
            console.print("[bold red]Warning: Unresolved type errors remain.[/bold red]\n")
    else:
        console.print("[bold green]✓ Type check passed cleanly![/bold green]\n")


async def _show_post_debate_menu(state: SessionState, console: Console) -> None:
    """Interactive single-keypress action prompt after deliverable is saved."""
    from prompt_toolkit.key_binding import KeyBindings
    from aztec_circle.tui.commands import cmd_build, cmd_start, cmd_test, cmd_fix

    console.print(
        "[bold]▶ Quick Actions:[/bold]  "
        "[bold cyan]\\[b][/bold cyan] Build & Bundle  "
        "[bold cyan]\\[r][/bold cyan] Start Live Server  "
        "[bold cyan]\\[t][/bold cyan] Run Tests  "
        "[bold cyan]\\[f][/bold cyan] Auto-Fix  "
        "[dim]\\[Enter] Next Prompt[/dim]"
    )
    kb = KeyBindings()
    action = {"value": None}

    @kb.add("b")
    def _b(event):
        action["value"] = "build"
        event.app.exit()

    @kb.add("r")
    def _r(event):
        action["value"] = "start"
        event.app.exit()

    @kb.add("t")
    def _t(event):
        action["value"] = "test"
        event.app.exit()

    @kb.add("f")
    def _f(event):
        action["value"] = "fix"
        event.app.exit()

    @kb.add("enter")
    @kb.add("escape")
    def _skip(event):
        event.app.exit()

    menu_session = PromptSession(key_bindings=kb)
    try:
        await menu_session.prompt_async("")
    except Exception:
        pass

    if action["value"] == "build":
        await cmd_build("", state, console)
    elif action["value"] == "start":
        await cmd_build("", state, console)
        await cmd_start("", state, console)
    elif action["value"] == "test":
        await cmd_test("", state, console)
    elif action["value"] == "fix":
        await cmd_fix("", state, console)


async def start_interactive_session() -> None:
    """Launch the interactive Aztec TUI session loop."""
    history_file = Path("~/.aztec_history").expanduser()
    state = SessionState()
    renderer = TranscriptRenderer(console)
    print_welcome_banner(console, state)

    main_kb = KeyBindings()

    @main_kb.add("c-v")
    def _handle_paste(event):
        try:
            from aztec_circle.adapters.clipboard_utils import get_clipboard_image
            from aztec_circle.adapters.image_utils import encode_image_to_data_uri

            clip_img = get_clipboard_image()
            if clip_img:
                data_uri = encode_image_to_data_uri(clip_img)
                state.attached_images.append(data_uri)
                console.print(f"\n[bold green]✓ Attached clipboard image:[/bold green] [underline]{clip_img}[/underline] [dim]({len(state.attached_images)} attached)[/dim]")
                event.app.invalidate()
                return
        except Exception:
            pass

        try:
            event.current_buffer.paste_clipboard_data(event.app.clipboard.get_data())
        except Exception:
            pass

    session: PromptSession = PromptSession(
        history=FileHistory(str(history_file)),
        completer=SlashCompleter(),
        key_bindings=main_kb,
        style=TUI_STYLE,
    )

    while True:
        try:
            prompt_str = state.prompt_text()
            user_input = await session.prompt_async(ANSI(prompt_str))
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Exiting Aztec session. Goodbye![/dim]")
            break

        cleaned = user_input.strip()
        if not cleaned:
            continue

        # Check if user input is a slash command
        is_cmd = await dispatch_slash_command(cleaned, state, console)
        if not is_cmd:
            if _is_modular_consensus_request(cleaned, state):
                # Requesting a major module / consensus on existing project
                await run_modular_consensus_session(cleaned, state, console)
            elif _is_edit_followup(cleaned, state):
                # Follow-up edit on existing project -> Run lightweight Edit Engine
                await run_edit_session(cleaned, state, console)
            else:
                # Free-text goal -> Launch full debate
                await run_debate_session(cleaned, state, renderer)
