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
    "/models": "View or reassign active models across agent ranks",
    "/policy": "Set or view fallback policy (HUMAN_IN_THE_LOOP / BEST_EFFORT / ABORT)",
    "/runs": "List recent checkpointed runs from SQLite database",
    "/resume": "Resume a past task run: /resume <task_id>",
    "/build": "Scaffold and build generated project (npm install && npm run build)",
    "/edit": "Apply an atomic targeted edit to the current project",
    "/rebuild": "Force a full debate cycle to regenerate project from scratch",
    "/fix": "Run automated self-healing build error repair on project",
    "/test": "Run project test suite (vitest / npm test / pytest)",
    "/start": "Launch live dev server (npm run dev) on port 5173",
    "/stop": "Stop active running background dev server",
    "/clear": "Clear the terminal screen",
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
