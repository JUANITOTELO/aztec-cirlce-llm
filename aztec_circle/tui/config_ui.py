"""
Interactive TUI Configuration Wizard, Model Catalog Browser, and Credential Manager.
"""

from __future__ import annotations

import asyncio
from typing import Optional
from prompt_toolkit import prompt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from aztec_circle.config import settings
from aztec_circle.domain.model_catalog import ModelCatalog, PRESET_CONFIGURATIONS, CURATED_MODELS
from aztec_circle.engine.config_manager import ConfigManager
from aztec_circle.tui.session import SessionState


def render_api_keys_table(console: Console) -> None:
    """Display Rich table of LLM provider API keys and their configuration status."""
    keys_data = ConfigManager.get_api_keys_status()
    table = Table(
        title="🔑 LLM Provider API Keys & Credentials",
        header_style="bold gold1",
        border_style="dim cyan",
        expand=True,
    )
    table.add_column("Environment Variable", style="bold cyan", width=22)
    table.add_column("Provider & Models", style="white", width=30)
    table.add_column("Status", justify="center", width=14)
    table.add_column("Masked Key Value", style="yellow", width=20)
    table.add_column("Get API Key", style="dim underline blue")

    for k in keys_data:
        status_badge = "[bold green]✓ Configured[/bold green]" if k["is_set"] else "[bold red]✗ Not Set[/bold red]"
        table.add_row(
            k["key_name"],
            k["provider"],
            status_badge,
            k["masked"],
            k["doc_url"],
        )

    console.print(table)
    cfg_path = ConfigManager.get_config_file_path()
    console.print(f"[dim]Keys are encrypted/stored with 0600 permissions in {cfg_path}[/dim]\n")


def render_ranks_table(console: Console) -> None:
    """Display current model assignments across agent ranks."""
    table = Table(
        title="🎭 Active Aztec Rank Model Assignments",
        header_style="bold gold1",
        border_style="dim cyan",
        expand=True,
    )
    table.add_column("Rank", style="bold cyan")
    table.add_column("Role / Responsibility", style="dim")
    table.add_column("Configured Model", style="bold green")
    table.add_column("Capabilities", style="magenta")
    table.add_column("Key Status", justify="center")

    ranks = [
        ("Youth", "Chaos Brainstorming & Devil's Advocate", settings.YOUTH_MODEL),
        ("Peer", "Synthesis, Architecture & Code Drafting", settings.PEER_MODEL),
        ("Elder", "Security Governance & Structural Audit", settings.ELDER_MODEL),
        ("Fallback", "Emergency Failover Redirection", str(settings.FALLBACK_MODEL or "None")),
    ]

    for rank_name, role_desc, model_id in ranks:
        info = ModelCatalog.get_model_info(model_id)
        caps = []
        if info.multimodal:
            caps.append("👁️ Vision")
        if info.reasoning:
            caps.append("🧠 Reasoning")
        if not caps:
            caps.append("⚡ Standard")

        key_status = "[green]✓ Ready[/green]" if info.is_configured else "[red]✗ Needs Key[/red]"
        table.add_row(
            rank_name,
            role_desc,
            model_id,
            " ".join(caps),
            key_status,
        )

    console.print(table)
    console.print()


def render_model_catalog_table(console: Console, provider: Optional[str] = None) -> None:
    """Display curated model catalog with LiteLLM capabilities."""
    models = ModelCatalog.list_curated_models(provider=provider)
    table = Table(
        title=f"📚 Curated Frontier Model Catalog {f'({provider.upper()})' if provider else ''}",
        header_style="bold gold1",
        border_style="dim cyan",
        expand=True,
    )
    table.add_column("Model ID", style="bold cyan", width=36)
    table.add_column("Display Name", style="white", width=22)
    table.add_column("Context", justify="right", style="dim", width=10)
    table.add_column("Capabilities", style="magenta", width=24)
    table.add_column("Recommended Ranks", style="bold yellow", width=20)
    table.add_column("Ready?", justify="center", width=10)

    for m in models:
        caps = []
        if m.multimodal:
            caps.append("👁️ Vision")
        if m.reasoning:
            caps.append("🧠 Reason")
        if m.supports_tools:
            caps.append("🔧 Tools")

        ready = "[green]✓[/green]" if m.is_configured else "[red]✗[/red]"
        table.add_row(
            m.id,
            m.name,
            f"{m.context_k}k",
            " ".join(caps),
            ", ".join(m.recommended_ranks),
            ready,
        )

    console.print(table)
    console.print()


def render_presets_table(console: Console) -> None:
    """Display pre-configured architecture presets."""
    table = Table(
        title="⚡ One-Click Architecture Presets",
        header_style="bold gold1",
        border_style="dim cyan",
        expand=True,
    )
    table.add_column("Preset ID", style="bold cyan", width=18)
    table.add_column("Preset Name", style="bold green", width=32)
    table.add_column("Description", style="dim")

    for pid, pdata in PRESET_CONFIGURATIONS.items():
        table.add_row(pid, pdata["name"], pdata["description"])

    console.print(table)
    console.print("[dim]Usage: /preset <preset_id>  (e.g., /preset max_reasoning)[/dim]\n")


async def run_test_models(console: Console) -> None:
    """Probe all active rank models with a 1-token test ping."""
    console.print("[bold cyan]🧪 Testing Model Connectivity & Latency across Active Ranks...[/bold cyan]\n")
    ranks = [
        ("Youth Rank", settings.YOUTH_MODEL),
        ("Peer Rank", settings.PEER_MODEL),
        ("Elder Rank", settings.ELDER_MODEL),
    ]
    if settings.FALLBACK_MODEL and settings.FALLBACK_MODEL != "None":
        ranks.append(("Fallback Rank", settings.FALLBACK_MODEL))

    table = Table(title="Model Ping Test Results", header_style="bold gold1", expand=True)
    table.add_column("Rank", style="bold cyan", width=16)
    table.add_column("Model ID", style="white", width=36)
    table.add_column("Status", justify="center", width=16)
    table.add_column("Latency", justify="right", width=12)
    table.add_column("Details", style="dim")

    for rank_label, model_id in ranks:
        with console.status(f"[dim]Pinging {rank_label} ({model_id})...[/dim]"):
            success, msg, latency = await ConfigManager.test_model_connection(model_id)

        status_str = "[bold green]✓ Online[/bold green]" if success else "[bold red]✗ Failed[/bold red]"
        lat_str = f"{latency:.2f}s" if latency > 0 else "-"
        table.add_row(rank_label, model_id, status_str, lat_str, msg)

    console.print(table)
    console.print()


async def run_interactive_config_menu(console: Console, state: SessionState) -> None:
    """Launch interactive configuration menu."""
    while True:
        console.print(Panel(
            "[bold cyan]Aztec Configuration Center[/bold cyan]\n\n"
            "[bold green]1.[/bold green] 🔑 [bold]Manage API Keys[/bold] (View & securely set API keys)\n"
            "[bold green]2.[/bold green] 🎭 [bold]Assign Models to Ranks[/bold] (Youth, Peer, Elder, Fallback)\n"
            "[bold green]3.[/bold green] 📚 [bold]Browse Model Catalog[/bold] (View capabilities & context)\n"
            "[bold green]4.[/bold green] ⚡ [bold]Apply Architecture Preset[/bold] (Speed, Reasoning, Google, OpenAI)\n"
            "[bold green]5.[/bold green] 🧪 [bold]Test Model Connections[/bold] (Live 1-token latency ping)\n"
            "[bold green]0.[/bold green] 🚪 [bold]Return to Main Session[/bold]",
            title="⚙️ Settings & Models",
            border_style="cyan",
        ))

        try:
            choice = prompt("Select an option (0-5): ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if choice == "0" or choice.lower() in ("exit", "q", "quit"):
            break

        elif choice == "1":
            render_api_keys_table(console)
            console.print("[dim]Enter the key name to set (e.g. GEMINI_API_KEY, ANTHROPIC_API_KEY) or press Enter to cancel:[/dim]")
            try:
                key_name = prompt("Key Name: ").strip().upper()
                if key_name:
                    new_val = prompt(f"Enter value for {key_name} (masked): ", is_password=True).strip()
                    if new_val:
                        ConfigManager.save_api_key(key_name, new_val)
                        console.print(f"[bold green]✓ Successfully updated and secured {key_name} in ~/.aztec/config.env[/bold green]\n")
            except (EOFError, KeyboardInterrupt):
                pass

        elif choice == "2":
            render_ranks_table(console)
            console.print("[dim]Select rank to update (YOUTH, PEER, ELDER, FALLBACK) or press Enter to cancel:[/dim]")
            try:
                rank_choice = prompt("Rank to update: ").strip().upper()
                if rank_choice in ("YOUTH", "PEER", "ELDER", "FALLBACK"):
                    new_model = prompt(f"New model for {rank_choice} (e.g. gemini/gemini-3.7-flash): ").strip()
                    if new_model:
                        ConfigManager.save_model_assignment(rank_choice, new_model)
                        if rank_choice == "PEER":
                            state.primary_model = new_model
                        console.print(f"[bold green]✓ Assigned {rank_choice} to {new_model}[/bold green]\n")
            except (EOFError, KeyboardInterrupt):
                pass

        elif choice == "3":
            render_model_catalog_table(console)

        elif choice == "4":
            render_presets_table(console)
            try:
                preset_id = prompt("Preset ID to apply: ").strip().lower()
                if preset_id in PRESET_CONFIGURATIONS:
                    ConfigManager.apply_preset(preset_id)
                    state.primary_model = settings.PEER_MODEL
                    console.print(f"[bold green]✓ Successfully applied preset: {PRESET_CONFIGURATIONS[preset_id]['name']}[/bold green]\n")
                elif preset_id:
                    console.print(f"[bold red]Unknown preset '{preset_id}'.[/bold red]\n")
            except (EOFError, KeyboardInterrupt):
                pass

        elif choice == "5":
            await run_test_models(console)
