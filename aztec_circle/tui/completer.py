"""
Auto-completer for Aztec TUI slash commands.
"""

from __future__ import annotations

from typing import Iterable
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

SLASH_COMMAND_METADATA = {
    "/help": "Show available commands and usage guide",
    "/status": "Display session stats, token spend, and active configuration",
    "/plasticity": "Inspect neuroplastic learning state: /plasticity [lessons|reset]",
    "/plan": "View, sync, or build a new module into living blueprint: /plan [sync|file|<goal>]",
    "/roadmap": "View project roadmap milestones and completion status",
    "/consensus": "Run multi-generational consensus debate for a new module or feature: /consensus <goal>",
    "/module": "Architect and integrate a new module with consensus: /module <goal>",
    "/feature": "Architect and integrate a new feature with consensus: /feature <goal>",
    "/debate": "Run Aztec debate consensus for a module: /debate <goal>",
    "/config": "Open interactive configuration center (keys, models, presets)",
    "/keys": "View and securely configure LLM provider API keys",
    "/models": "View or reassign active models across agent ranks",
    "/preset": "Apply one-click architecture preset: /preset <name>",
    "/test-models": "Probe active rank models with a live latency ping",
    "/policy": "Set or view fallback policy (HUMAN_IN_THE_LOOP / BEST_EFFORT / ABORT)",
    "/budget": "Set or view per-task USD budget limit: /budget [amount]",
    "/runs": "List recent checkpointed runs from SQLite database",
    "/resume": "Resume a past task run: /resume <task_id>",
    "/build": "Scaffold and build generated project (npm install && npm run build)",
    "/edit": "Apply an atomic targeted edit to the current project",
    "/rebuild": "Force a full debate cycle to regenerate project from scratch",
    "/fix": "Run automated self-healing build error repair on project",
    "/test": "Run project test suite (vitest / npm test / pytest)",
    "/start": "Launch live dev server (npm run dev) on port 5173",
    "/stop": "Stop active running background dev server",
    "/run": "Execute console/shell command with streaming output: /run <command>",
    "/sh": "Execute console/shell command: /sh <command>",
    "/exec": "Execute console/shell command: /exec <command>",
    "/cmd": "Execute console/shell command: /cmd <command>",
    "/php": "Execute PHP script or command: /php <args>",
    "/mysql": "Execute MySQL command or script: /mysql <args>",
    "/sqlite": "Execute SQLite command or query: /sqlite [db_file] <query_or_file>",
    "/db": "Execute database/SQLite command: /db [db_file] <query_or_file>",
    "/logs": "View background development server output logs",
    "/clear": "Clear the terminal screen",
    "/image": "Attach reference image to session: /image <path_or_url>",
    "/paste": "Grab and attach image from system clipboard (Ctrl+V)",
    "/paste-image": "Grab and attach image from system clipboard (Ctrl+V)",
    "/images": "List all attached reference images in the active session",
    "/clear-images": "Remove all attached images from the active session",
    "/update": "Check for and apply latest Aztec framework updates",
    "/exit": "Exit interactive Aztec session",
    "/quit": "Exit interactive Aztec session",
}


class SlashCompleter(Completer):
    """Provides auto-completion for slash commands in prompt_toolkit."""

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        text_before = document.text_before_cursor
        if text_before.startswith("/"):
            query = text_before.lower()
            for cmd, desc in SLASH_COMMAND_METADATA.items():
                if cmd.startswith(query):
                    yield Completion(
                        cmd,
                        start_position=-len(text_before),
                        display=cmd,
                        display_meta=desc,
                    )
