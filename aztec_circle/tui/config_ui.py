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
    """Display current model assignments across all ranks and granular sub-roles."""
    table = Table(
        title="🎭 Active Aztec Rank & Role Model Assignments",
        header_style="bold gold1",
        border_style="dim cyan",
        expand=True,
    )
    table.add_column("Rank / Group", style="bold cyan", width=14)
    table.add_column("Role & Responsibility", style="white", width=30)
    table.add_column("Role Key", style="dim yellow", width=18)
    table.add_column("Effective Model", style="bold green", width=30)
    table.add_column("Inheritance", justify="center", width=14)
    table.add_column("Capabilities", style="magenta", width=18)
    table.add_column("Key Status", justify="center", width=12)

    roles = ConfigManager.get_granular_roles_status()

    for r in roles:
        info = r["model_info"]
        caps = []
        if info.multimodal:
            caps.append("👁️ Vision")
        if info.reasoning:
            caps.append("🧠 Reason")
        if not caps:
            caps.append("⚡ Speed")

        key_status = "[green]✓ Ready[/green]" if info.is_configured else "[red]✗ Needs Key[/red]"
        inherit_badge = "[cyan]Override[/cyan]" if r["is_override"] else "[dim]Rank Default[/dim]" if r["rank_group"] != "AUXILIARY" else "[dim]Auxiliary[/dim]"

        table.add_row(
            r["rank_group"],
            r["role_label"],
            r["role_key"],
            r["effective_model"],
            inherit_badge,
            " ".join(caps),
            key_status,
        )

    console.print(table)
    console.print("[dim]Assign via: /models <ROLE_KEY> <MODEL_ID> (e.g. /models ELDER_SECURITY deepseek/deepseek-r1)[/dim]")
    console.print("[dim]Reset via:  /models reset <ROLE_KEY> (e.g. /models reset ELDER_SECURITY)[/dim]\n")


def render_model_catalog_table(console: Console, provider: Optional[str] = None) -> None:
    """Display curated model catalog with LiteLLM capabilities."""
    models = ModelCatalog.list_curated_models(provider=provider)
    table = Table(
        title=f"📚 Curated Frontier Model Catalog {f'({provider.upper()})' if provider else ''}",
        header_style="bold gold1",
        border_style="dim cyan",
        expand=True,
    )
    table.add_column("Index", justify="right", style="bold cyan", width=6)
    table.add_column("Model ID", style="bold cyan", width=32)
    table.add_column("Display Name", style="white", width=22)
    table.add_column("Context", justify="right", style="dim", width=10)
    table.add_column("Capabilities", style="magenta", width=20)
    table.add_column("Pricing (In / Out)", style="dim green", width=18)
    table.add_column("Ready?", justify="center", width=8)

    for idx, m in enumerate(models, 1):
        caps = []
        if m.multimodal:
            caps.append("👁️")
        if m.reasoning:
            caps.append("🧠")
        if m.supports_tools:
            caps.append("🔧")

        pricing = ModelCatalog.get_model_pricing(m.id)
        price_str = f"${pricing[0]:.2f} / ${pricing[1]:.2f}"
        ready = "[green]✓[/green]" if m.is_configured else "[red]✗[/red]"

        table.add_row(
            str(idx),
            m.id,
            m.name,
            f"{m.context_k}k",
            " ".join(caps),
            price_str,
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
    table.add_column("Preset ID", style="bold cyan", width=24)
    table.add_column("Preset Name", style="bold green", width=36)
    table.add_column("Description", style="dim")

    for pid, pdata in PRESET_CONFIGURATIONS.items():
        table.add_row(pid, pdata["name"], pdata["description"])

    console.print(table)
    console.print("[dim]Usage: /preset <preset_id>  (e.g., /preset anthropic_efficiency)[/dim]\n")


async def run_interactive_role_picker(console: Console, state: SessionState) -> None:
    """Prompt user with numbered menus to assign models to specific roles."""
    roles = ConfigManager.get_granular_roles_status()
    
    console.print(Panel(
        "[bold cyan]Select Role to Configure:[/bold cyan]\n\n" +
        "\n".join(f"[bold green]{idx}.[/bold green] [bold]{r['role_label']}[/bold] [dim]({r['role_key']} -> {r['effective_model']})[/dim]" for idx, r in enumerate(roles, 1)) +
        "\n\n[bold green]0.[/bold green] [bold]Cancel[/bold]",
        title="🎭 Select Aztec Role",
        border_style="cyan",
    ))

    try:
        choice = prompt("Select role number (0-10): ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not choice.isdigit() or int(choice) == 0 or int(choice) > len(roles):
        return

    selected_role = roles[int(choice) - 1]
    role_key = selected_role["role_key"]

    # Show Curated Models Menu
    models = ModelCatalog.list_curated_models()
    console.print(Panel(
        f"[bold cyan]Assign Model to {selected_role['role_label']}:[/bold cyan]\n\n" +
        "\n".join(f"[bold green]{idx}.[/bold green] [bold]{m.name}[/bold] [dim]({m.id})[/dim]" for idx, m in enumerate(models, 1)) +
        "\n\n[dim]Or enter any custom model ID (e.g. anthropic/claude-sonnet-5, ollama/deepseek-r1:8b), 'reset' to inherit, or 0 to cancel.[/dim]",
        title=f"🤖 Choose Model for {role_key}",
        border_style="cyan",
    ))

    try:
        model_choice = prompt(f"Model for {role_key}: ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    if not model_choice or model_choice == "0":
        return

    if model_choice.lower() in ("reset", "inherit", "default", "none"):
        ConfigManager.reset_model_assignment(role_key)
        console.print(f"[bold green]✓ Reset {role_key} to inherit from rank default.[/bold green]\n")
        return

    if model_choice.isdigit() and 1 <= int(model_choice) <= len(models):
        target_model = models[int(model_choice) - 1].id
    else:
        target_model = model_choice

    ConfigManager.save_model_assignment(role_key, target_model)
    if role_key == "PEER":
        state.primary_model = target_model

    console.print(f"[bold green]✓ Assigned {role_key} to {target_model}[/bold green]\n")


async def run_test_models(console: Console) -> None:
    """Probe all active unique rank and role models with a 1-token test ping."""
    console.print("[bold cyan]🧪 Testing Model Connectivity & Latency across Active Ranks & Roles...[/bold cyan]\n")
    
    roles = ConfigManager.get_granular_roles_status()
    # Unique effective models
    seen_models = set()
    test_targets = []
    for r in roles:
        eff = r["effective_model"]
        if eff and eff not in seen_models and eff != "None":
            seen_models.add(eff)
            test_targets.append((r["role_label"], eff))

    table = Table(title="Model Ping Test Results", header_style="bold gold1", expand=True)
    table.add_column("Role Sample", style="bold cyan", width=28)
    table.add_column("Model ID", style="white", width=36)
    table.add_column("Status", justify="center", width=16)
    table.add_column("Latency", justify="right", width=12)
    table.add_column("Details", style="dim")

    for role_label, model_id in test_targets:
        with console.status(f"[dim]Pinging {role_label} ({model_id})...[/dim]"):
            success, msg, latency = await ConfigManager.test_model_connection(model_id)

        status_str = "[bold green]✓ Online[/bold green]" if success else "[bold red]✗ Failed[/bold red]"
        lat_str = f"{latency:.2f}s" if latency > 0 else "-"
        table.add_row(role_label, model_id, status_str, lat_str, msg)

    console.print(table)
    console.print()


async def run_interactive_config_menu(console: Console, state: SessionState) -> None:
    """Launch interactive configuration menu."""
    while True:
        console.print(Panel(
            "[bold cyan]Aztec Configuration Center[/bold cyan]\n\n"
            "[bold green]1.[/bold green] 🔑 [bold]Manage API Keys[/bold] (View & securely set API keys)\n"
            "[bold green]2.[/bold green] 🎭 [bold]Assign Models to Roles & Ranks[/bold] (Granular role model picker)\n"
            "[bold green]3.[/bold green] 📚 [bold]Browse Model Catalog[/bold] (View capabilities & context)\n"
            "[bold green]4.[/bold green] ⚡ [bold]Apply Architecture Preset[/bold] (Anthropic, Speed, Reasoning, OpenAI)\n"
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
            await run_interactive_role_picker(console, state)

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

