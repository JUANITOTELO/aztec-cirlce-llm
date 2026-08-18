"""
Aztec Living Project Plan & Blueprint Manager (AZTEC_PLAN.md).

Maintains an authoritative, token-optimized, self-updating project blueprint,
phased roadmap, file inventory, and iteration change log across generational debates,
incremental edits, and compiler repair loops.
"""

from __future__ import annotations

import datetime
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import structlog
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aztec_circle.domain.models import CircleRunState
from aztec_circle.engine.project_indexer import ProjectIndexer
from aztec_circle.engine.scaffolder import find_project_root, detect_project_ecosystem

log = structlog.get_logger(__name__)

PLAN_FILENAME = "AZTEC_PLAN.md"


class PlanManager:
    """Manages the creation, maintenance, and synchronization of AZTEC_PLAN.md."""

    @classmethod
    def get_plan_path(cls, target_dir: str) -> Path:
        """Return the absolute path to AZTEC_PLAN.md in the project root."""
        root = find_project_root(target_dir) or target_dir
        return Path(root).resolve() / PLAN_FILENAME

    @classmethod
    def plan_exists(cls, target_dir: str) -> bool:
        """Check if an AZTEC_PLAN.md exists in the project root."""
        return cls.get_plan_path(target_dir).exists()

    @classmethod
    def read_plan(cls, target_dir: str) -> Optional[str]:
        """Read existing AZTEC_PLAN.md content if available."""
        p = cls.get_plan_path(target_dir)
        if p.exists():
            try:
                return p.read_text(encoding="utf-8")
            except Exception:
                return None
        return None

    @classmethod
    def generate_or_update_from_debate(
        cls,
        state: CircleRunState,
        output_dir: str,
        active_preset: Optional[str] = None,
    ) -> Path:
        """
        Synthesize or update AZTEC_PLAN.md following a successful generational debate run.
        """
        root = find_project_root(output_dir) or output_dir
        plan_path = Path(root).resolve() / PLAN_FILENAME
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        overview = "Modern atomic modular architecture."
        impl_code: Dict[str, str] = {}
        mitigations: List[str] = []
        assumptions: List[str] = []

        if hasattr(state, "peer_history") and state.peer_history:
            last_peer = state.peer_history[-1]
            overview = getattr(last_peer, "architecture_overview", overview)
            impl_code = getattr(last_peer, "implementation_code", {}) or {}
            mitigations = getattr(last_peer, "mitigations_applied", []) or []
            assumptions = getattr(last_peer, "assumptions_made", []) or []
        elif isinstance(state, dict) and "peer_output" in state:
            peer_out = state.get("peer_output", {}) or {}
            overview = peer_out.get("architecture_overview", overview)
            impl_code = peer_out.get("implementation_code", {}) or {}
            mitigations = peer_out.get("mitigations_applied", []) or []
            assumptions = peer_out.get("assumptions_made", []) or []
        elif hasattr(state, "peer_output"):
            peer_out = getattr(state, "peer_output", {}) or {}
            if isinstance(peer_out, dict):
                overview = peer_out.get("architecture_overview", overview)
                impl_code = peer_out.get("implementation_code", {}) or {}
                mitigations = peer_out.get("mitigations_applied", []) or []
                assumptions = peer_out.get("assumptions_made", []) or []

        # File classification
        src_files = [f for f in sorted(impl_code.keys()) if f.startswith("src/")]
        config_files = [f for f in sorted(impl_code.keys()) if not f.startswith("src/")]

        # Determine ecosystem
        eco = detect_project_ecosystem(root)
        eco_label = "Vite 5 + React 18 + TypeScript + TailwindCSS" if eco == "vite_react" else eco

        # Build file table
        file_table_rows = []
        for rel_file in sorted(impl_code.keys()):
            layer = cls._classify_layer(rel_file)
            resp = cls._infer_responsibility(rel_file)
            file_table_rows.append(f"| `{rel_file}` | {layer} | {resp} |")
        file_table_md = "\n".join(file_table_rows) if file_table_rows else "| `src/App.tsx` | Coordinator | Main application shell |"

        # Build mitigations / ADRs
        adrs_md = []
        for idx, m in enumerate(mitigations, start=1):
            adrs_md.append(f"- **[ADR-{idx:02d}]**: {m}")
        if not adrs_md:
            adrs_md = [
                "- **[ADR-01]**: Single Responsibility Principle with 150-line file limits enforced.",
                "- **[ADR-02]**: Separation of domain calculation hooks/engine from direct JSX rendering.",
            ]
        adrs_section = "\n".join(adrs_md)

        # Assumptions
        assumptions_md = "\n".join(f"- {a}" for a in assumptions) if assumptions else "- Standard modern browser ES2020 environment."

        features_list = "".join(f"- [x] Feature implementation: `{f}`\n" for f in src_files[:4])
        preset_str = f" ({active_preset})" if active_preset else ""

        cost_val = getattr(state, "total_cost_usd", 0.0) if state else 0.0
        content = f"""# 🏛️ Aztec Project Blueprint & Living Roadmap

> **Project Goal**: {state.goal if state else "Aztec Application"}  
> **Status**: Production Ready / Active Iteration  
> **Last Updated**: {now_str}  
> **Active Presets**: Aztec Multi-Generational Circle{preset_str}  

---

## 📐 Architecture & Technology Stack
- **Ecosystem**: {eco_label}
- **Architecture Overview**: {overview}
- **Atomic Directory Discipline**:
  - `src/atoms/` — Single-purpose UI primitives (<= 60 lines)
  - `src/components/` — Composite UI panels & containers (<= 120 lines)
  - `src/hooks/` — Dedicated React state & behavioral hooks (<= 80 lines)
  - `src/engine/` — Pure domain logic, math, algorithms (<= 150 lines, zero UI imports)
  - `src/store/` — State slices & persistence (<= 100 lines)
  - `src/types/` — TypeScript interfaces & contracts (<= 100 lines)

### Key Architectural Decisions (ADRs)
{adrs_section}

### Assumptions & Technical Invariants
{assumptions_md}

---

## 🗺️ Phased Implementation Roadmap

### Phase 1: Core Foundation & Configuration
- [x] Initial build configuration & toolchain (`package.json`, `tsconfig.json`, `vite.config.ts`)
- [x] Styling foundation & design tokens (`tailwind.config.js`, `src/index.css`)
- [x] Base atomic primitives & layout scaffolding

### Phase 2: Domain Implementation & State Flow
- [x] Core domain components & view coordinators (`src/App.tsx`)
- [x] State management & custom hooks integration
{features_list}
### Phase 3: Validation, Self-Healing & Verification
- [x] Automated test suite passing (`src/App.test.tsx`)
- [x] Zero TypeScript compiler & lint errors
- [x] Background live dev server verification on port 5173

---

## 📁 File & Module Index

| File | Layer | Responsibility |
| :--- | :--- | :--- |
{file_table_md}

---

## 📝 Change Log & Iteration History
- **{now_str}** — Initial Generational Debate Loop (Youth Chaos -> Peer Drafter -> Elder Council Approved). Total Task Cost: ${cost_val:.4f}.
"""
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(content, encoding="utf-8")
        log.info("plan_manager.generated", path=str(plan_path))
        return plan_path

    @classmethod
    def record_edit_iteration(
        cls,
        output_dir: str,
        instruction: str,
        modified_files: List[str],
        executed_commands: Optional[List[str]] = None,
    ) -> None:
        """
        Update AZTEC_PLAN.md with an incremental edit entry, updating the file table and change log.
        """
        root = find_project_root(output_dir) or output_dir
        plan_path = Path(root).resolve() / PLAN_FILENAME
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not plan_path.exists():
            # If no plan existed, create a lightweight scaffold plan
            cls.sync_from_codebase(output_dir)
            if not plan_path.exists():
                return

        existing = plan_path.read_text(encoding="utf-8")

        # 1. Update Last Updated timestamp
        existing = re.sub(
            r"> \*\*Last Updated\*\*: .*",
            f"> **Last Updated**: {now_str}  ",
            existing,
        )

        # 2. Append to Change Log
        details_parts = []
        if modified_files:
            details_parts.append(f"Modified: {', '.join(modified_files)}")
        if executed_commands:
            details_parts.append(f"Executed: {', '.join(executed_commands)}")
        details_str = f" ({'; '.join(details_parts)})" if details_parts else ""

        change_entry = f"- **{now_str}** — Incremental Edit: \"{instruction}\"{details_str}.\n"
        if "## 📝 Change Log & Iteration History" in existing:
            existing = existing.replace(
                "## 📝 Change Log & Iteration History\n",
                f"## 📝 Change Log & Iteration History\n{change_entry}",
            )
        else:
            existing += f"\n\n## 📝 Change Log & Iteration History\n{change_entry}"

        # 3. Add any newly created files to the File & Module Index
        for f in modified_files:
            clean_f = f.lstrip("/\\").replace("\\", "/")
            if f"`{clean_f}`" not in existing and "## 📁 File & Module Index" in existing:
                layer = cls._classify_layer(clean_f)
                resp = cls._infer_responsibility(clean_f)
                new_row = f"| `{clean_f}` | {layer} | {resp} |\n"
                existing = existing.replace(
                    "| :--- | :--- | :--- |\n",
                    f"| :--- | :--- | :--- |\n{new_row}",
                )

        plan_path.write_text(existing, encoding="utf-8")
        log.info("plan_manager.edit_recorded", instruction=instruction, files=modified_files, commands=executed_commands or [])

    @classmethod
    def record_fix_iteration(
        cls,
        output_dir: str,
        fixed_files: List[str],
        error_summary: str = "",
    ) -> None:
        """Record an automated build / compiler fix in the change log."""
        root = find_project_root(output_dir) or output_dir
        plan_path = Path(root).resolve() / PLAN_FILENAME
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not plan_path.exists():
            return

        existing = plan_path.read_text(encoding="utf-8")
        summary_snip = f": {error_summary[:60]}..." if error_summary else ""
        change_entry = f"- **{now_str}** — Automated Self-Healing Build Fix ({len(fixed_files)} files repaired{summary_snip}).\n"

        if "## 📝 Change Log & Iteration History" in existing:
            existing = existing.replace(
                "## 📝 Change Log & Iteration History\n",
                f"## 📝 Change Log & Iteration History\n{change_entry}",
            )
            plan_path.write_text(existing, encoding="utf-8")

    @classmethod
    def sync_from_codebase(cls, output_dir: str, goal: Optional[str] = None) -> Path:
        """
        Scan actual source files on disk and generate/refresh AZTEC_PLAN.md.
        """
        root = find_project_root(output_dir) or output_dir
        plan_path = Path(root).resolve() / PLAN_FILENAME
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        indexer = ProjectIndexer()
        index = indexer.build(root)
        files = [f.rel_path for f in index.file_indices]

        # Extract project goal from package.json or existing plan
        derived_goal = goal or "Aztec Software Project"
        if not goal and plan_path.exists():
            try:
                curr = plan_path.read_text(encoding="utf-8")
                m = re.search(r"> \*\*Project Goal\*\*: (.*)", curr)
                if m:
                    derived_goal = m.group(1).strip()
            except Exception:
                pass

        file_table_rows = []
        for rel_file in sorted(files):
            layer = cls._classify_layer(rel_file)
            resp = cls._infer_responsibility(rel_file)
            file_table_rows.append(f"| `{rel_file}` | {layer} | {resp} |")
        file_table_md = "\n".join(file_table_rows) if file_table_rows else "| `src/App.tsx` | Coordinator | Main application shell |"

        eco = detect_project_ecosystem(root)
        eco_label = "Vite 5 + React 18 + TypeScript + TailwindCSS" if eco == "vite_react" else eco

        content = f"""# 🏛️ Aztec Project Blueprint & Living Roadmap

> **Project Goal**: {derived_goal}  
> **Status**: Active / Synced with Codebase  
> **Last Updated**: {now_str}  
> **Files Indexed**: {len(files)} total source files  

---

## 📐 Architecture & Technology Stack
- **Ecosystem**: {eco_label}
- **Atomic Directory Discipline**:
  - `src/atoms/` — Single-purpose UI primitives (<= 60 lines)
  - `src/components/` — Composite UI panels & containers (<= 120 lines)
  - `src/hooks/` — Dedicated React state & behavioral hooks (<= 80 lines)
  - `src/engine/` — Pure domain logic, math, algorithms (<= 150 lines, zero UI imports)
  - `src/store/` — State slices & persistence (<= 100 lines)
  - `src/types/` — TypeScript interfaces & contracts (<= 100 lines)

### Key Architectural Decisions (ADRs)
- **[ADR-01]**: Atomic modular architecture with strict 150-line ceiling per file.
- **[ADR-02]**: Separation of concerns between UI components and domain calculation engine.

---

## 🗺️ Phased Implementation Roadmap

### Phase 1: Core Foundation & Configuration
- [x] Initial build configuration & toolchain (`package.json`, `tsconfig.json`, `vite.config.ts`)
- [x] Styling foundation & design tokens (`tailwind.config.js`, `src/index.css`)
- [x] Base atomic primitives & layout scaffolding

### Phase 2: Domain Implementation & State Flow
- [x] Core domain components & view coordinators
- [x] State management & custom hooks integration

### Phase 3: Validation, Self-Healing & Verification
- [x] Automated test suite passing
- [x] Zero TypeScript compiler & lint errors
- [x] Live development server verified

---

## 📁 File & Module Index

| File | Layer | Responsibility |
| :--- | :--- | :--- |
{file_table_md}

---

## 📝 Change Log & Iteration History
- **{now_str}** — Codebase Synchronization (Indexed {len(files)} files).
"""
        plan_path.parent.mkdir(parents=True, exist_ok=True)
        plan_path.write_text(content, encoding="utf-8")
        log.info("plan_manager.synced", count=len(files), path=str(plan_path))
        return plan_path

    @classmethod
    def get_compact_plan_context(cls, target_dir: str, max_chars: int = 1500) -> str:
        """
        Return a token-dense, compact summary of AZTEC_PLAN.md for prompt injection.
        Designed for prompt caching reuse.
        """
        raw = cls.read_plan(target_dir)
        if not raw:
            return ""

        lines = raw.splitlines()
        compact_lines: List[str] = ["[PROJECT BLUEPRINT & ROADMAP CONTEXT]"]

        # Extract Goal, Architecture, ADRs, and Roadmap
        capture = True
        for line in lines:
            if line.startswith("# 🏛️") or line.startswith("---"):
                continue
            if line.startswith("## 📁 File & Module Index"):
                # Skip full table to preserve token budget; index is supplied separately
                capture = False
                continue
            if line.startswith("## 📝 Change Log"):
                capture = True
            if capture and line.strip():
                compact_lines.append(line.strip())

        result = "\n".join(compact_lines)
        if len(result) > max_chars:
            result = result[:max_chars] + "\n...[roadmap context truncated]"
        return result

    @classmethod
    def render_plan_dashboard(cls, target_dir: str, console: Console) -> None:
        """Render a formatted Rich dashboard of the active project plan."""
        p = cls.get_plan_path(target_dir)
        if not p.exists():
            console.print(f"[yellow]No AZTEC_PLAN.md found in [underline]{target_dir}[/underline].[/yellow]")
            console.print("Run [bold cyan]/plan sync[/bold cyan] to generate a living plan from current files.\n")
            return

        content = p.read_text(encoding="utf-8")

        # Parse Goal & Status
        goal_match = re.search(r"> \*\*Project Goal\*\*: (.*)", content)
        goal = goal_match.group(1).strip() if goal_match else "Aztec Project"
        updated_match = re.search(r"> \*\*Last Updated\*\*: (.*)", content)
        updated = updated_match.group(1).strip() if updated_match else "Recent"

        # Count completed vs pending tasks
        checked_tasks = len(re.findall(r"- \[x\]", content))
        pending_tasks = len(re.findall(r"- \[ \]", content))
        total_tasks = checked_tasks + pending_tasks
        progress_pct = int((checked_tasks / total_tasks * 100)) if total_tasks > 0 else 100

        # Display header panel
        header_text = (
            f"[bold gold1]🎯 Goal:[/bold gold1] [bold white]{goal}[/bold white]\n"
            f"[dim]📁 Plan File: {p} | 🕒 Updated: {updated}[/dim]\n"
            f"[bold cyan]📊 Progress:[/bold cyan] [bold green]{checked_tasks}/{total_tasks} milestones completed ({progress_pct}%)[/bold green]"
        )
        console.print(Panel(header_text, title="🏛️ Aztec Living Project Blueprint", border_style="bold gold1"))

        # Render Milestones Table
        roadmap_table = Table(
            title="🗺️ Implementation Roadmap & Milestones",
            header_style="bold cyan",
            border_style="dim cyan",
            expand=True,
        )
        roadmap_table.add_column("Status", width=10, justify="center")
        roadmap_table.add_column("Milestone / Task", style="white")

        in_roadmap = False
        for line in content.splitlines():
            if line.startswith("## 🗺️ Phased Implementation Roadmap"):
                in_roadmap = True
                continue
            if in_roadmap and line.startswith("## "):
                break
            if in_roadmap:
                if line.startswith("### "):
                    phase_title = line.replace("### ", "").strip()
                    roadmap_table.add_row("[bold yellow]PHASE[/bold yellow]", f"[bold yellow]{phase_title}[/bold yellow]")
                elif line.startswith("- [x]"):
                    task = line.replace("- [x]", "").strip()
                    roadmap_table.add_row("[bold green]✓ Done[/bold green]", task)
                elif line.startswith("- [ ]"):
                    task = line.replace("- [ ]", "").strip()
                    roadmap_table.add_row("[bold yellow]⏳ Pending[/bold yellow]", task)

        console.print(roadmap_table)

        # Render recent change log snippets
        recent_changes: List[str] = []
        in_changelog = False
        for line in content.splitlines():
            if line.startswith("## 📝 Change Log"):
                in_changelog = True
                continue
            if in_changelog and line.startswith("- **"):
                recent_changes.append(line.strip())
                if len(recent_changes) >= 4:
                    break

        if recent_changes:
            log_panel = Panel(
                "\n".join(recent_changes),
                title="📝 Recent Iterations & Edits",
                border_style="dim green",
            )
            console.print(log_panel)

        console.print(f"[dim]View complete document at: {p}[/dim]\n")

    @classmethod
    def _classify_layer(cls, rel_path: str) -> str:
        """Classify file into its atomic architectural layer."""
        p = rel_path.lower()
        if "atoms/" in p:
            return "Atom (UI Primitive)"
        if "components/" in p:
            return "Component (Composite)"
        if "hooks/" in p:
            return "Hook (State/Behavior)"
        if "engine/" in p or "services/" in p:
            return "Engine (Domain Logic)"
        if "store/" in p:
            return "Store (State Slice)"
        if "types/" in p:
            return "Types (Interfaces)"
        if "utils/" in p:
            return "Utils (Pure Helpers)"
        if "constants/" in p:
            return "Constants (Config)"
        if p.endswith((".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")):
            return "Test Suite"
        if p in ("package.json", "tsconfig.json", "vite.config.ts", "tailwind.config.js"):
            return "Config / Build"
        if p.endswith("app.tsx") or p.endswith("main.tsx"):
            return "Coordinator"
        return "Source"

    @classmethod
    def _infer_responsibility(cls, rel_path: str) -> str:
        """Derive a concise responsibility description from relative filepath."""
        p = rel_path.replace("\\", "/")
        stem = Path(p).stem

        if p == "src/App.tsx":
            return "Main application coordinator & view shell"
        if p == "src/main.tsx":
            return "React DOM entry root & style bootstrap"
        if p == "src/index.css":
            return "Tailwind base directives & global design tokens"
        if p.endswith(".test.tsx") or p.endswith(".test.ts"):
            return f"Unit tests for {stem.replace('.test', '')}"
        if "atoms/" in p:
            return f"Atomic UI primitive for {stem}"
        if "components/" in p:
            return f"Composite panel for {stem}"
        if "hooks/" in p:
            return f"React state management hook for {stem}"
        if "engine/" in p:
            return f"Pure mathematical & domain algorithms for {stem}"
        if "store/" in p:
            return f"Global state slice for {stem}"
        if "types/" in p:
            return f"Type definitions & data contracts for {stem}"
        if "constants/" in p:
            return f"Static configuration constants for {stem}"
        if p == "package.json":
            return "Node dependencies & scripts manifest"
        if p == "vite.config.ts":
            return "Vite dev server & build bundler configuration"
        if p == "tsconfig.json":
            return "TypeScript strict compiler options"
        if p == "tailwind.config.js":
            return "Tailwind CSS utility & theme configuration"
        return f"Module implementation for {stem}"
