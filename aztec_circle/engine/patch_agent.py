"""
Patch Agent and Applicator for Aztec Incremental Edit Engine.
Executes precision, token-efficient 2-round code edits using atomic line-range patches.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple
import structlog
from rich.console import Console

from aztec_circle.adapters.llm_provider import LLMProvider, LLMResponse
from aztec_circle.agents.base import extract_json_payload
from aztec_circle.config import settings
from aztec_circle.domain.models import ConsoleCommand, CommandExecutionResult
from aztec_circle.engine.ast_validator import ASTValidator
from aztec_circle.engine.budget_manager import BudgetManager
from aztec_circle.engine.project_indexer import ProjectIndex, ProjectIndexer
from aztec_circle.engine.scaffolder import find_project_root
from aztec_circle.prompts import render

log = structlog.get_logger(__name__)


@dataclass
class FilePatch:
    """Represents a single atomic mutation to a project file."""
    file: str
    action: str  # 'replace' | 'insert_before' | 'insert_after' | 'create' | 'delete'
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    replacement: Optional[str] = None
    concern: str = "Code modification"


@dataclass
class PatchResult:
    """Outcome of an incremental edit operation."""
    success: bool
    edit_summary: str
    patches: List[FilePatch] = field(default_factory=list)
    files_touched: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    commands_proposed: List[ConsoleCommand] = field(default_factory=list)
    commands_executed: List[CommandExecutionResult] = field(default_factory=list)
    round1_tokens: int = 0
    round2_tokens: int = 0
    total_cost_usd: float = 0.0
    error_message: Optional[str] = None


def _clean_rel_path(val: Any) -> str:
    """Safely convert any file specifier (str, int, Path, None) to a normalized relative path."""
    if val is None:
        return ""
    return str(val).strip().lstrip("/\\").replace("\\", "/")


def _safe_int(val: Any) -> Optional[int]:
    """Safely parse line number from int, numeric string, or None."""
    if val is None:
        return None
    if isinstance(val, int):
        return val
    val_str = str(val).strip()
    if val_str.isdigit():
        return int(val_str)
    return None


@dataclass
class EditStage:
    """Represents a grouped stage of files to modify in sequence."""
    stage_number: int
    name: str
    target_files: List[str]
    reference_files: List[str] = field(default_factory=list)


class PatchApplicator:
    """
    Applies structured patches to the filesystem with full atomic rollback on error.
    """

    @staticmethod
    def rollback(project_root: str, backups: Dict[str, Optional[str]]) -> None:
        """Restores original file state for all registered backups."""
        root = find_project_root(project_root)
        for clean_rel, original_content in backups.items():
            full_path = os.path.join(root, clean_rel)
            if original_content is None:
                if os.path.exists(full_path):
                    try:
                        os.remove(full_path)
                    except Exception:
                        pass
            else:
                try:
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as fh:
                        fh.write(original_content)
                except Exception:
                    pass

    @classmethod
    def apply(
        cls,
        project_root: str,
        patches: List[FilePatch],
        existing_backups: Optional[Dict[str, Optional[str]]] = None,
        topo_order: Optional[List[str]] = None,
        ast_validator: Optional[ASTValidator] = None,
    ) -> Tuple[List[str], List[str], List[str]]:
        """
        Apply patches atomically. Returns (files_touched, files_created, files_deleted).
        If any patch operation fails, rolls back all modified/created/deleted files.
        """
        root = find_project_root(project_root)
        backups: Dict[str, Optional[str]] = existing_backups if existing_backups is not None else {}
        touched: List[str] = []
        created: List[str] = []
        deleted: List[str] = []

        # 1. Capture backups of all affected files (if not already captured)
        for patch in patches:
            clean_rel = _clean_rel_path(patch.file)
            if not clean_rel:
                continue
            full_path = os.path.join(root, clean_rel)
            if clean_rel not in backups:
                if os.path.exists(full_path):
                    with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                        backups[clean_rel] = fh.read()
                else:
                    backups[clean_rel] = None

        # 2. Group patches by file
        patches_by_file: Dict[str, List[FilePatch]] = {}
        for p in patches:
            clean_rel = _clean_rel_path(p.file)
            if clean_rel:
                patches_by_file.setdefault(clean_rel, []).append(p)

        # 3. Sort files by topological order if provided
        if topo_order:
            order_map = {f: i for i, f in enumerate(topo_order)}
            sorted_files = sorted(patches_by_file.keys(), key=lambda f: order_map.get(f, 999))
        else:
            sorted_files = list(patches_by_file.keys())

        try:
            for clean_rel in sorted_files:
                file_patches = patches_by_file[clean_rel]
                full_path = os.path.join(root, clean_rel)

                for patch in file_patches:
                    action = (str(patch.action) if patch.action else "replace").lower()

                    if ast_validator and patch.replacement and action in ("create", "replace"):
                        val_res = ast_validator.validate(patch.replacement, clean_rel)
                        if not val_res.is_valid and val_res.errors:
                            log.warning(
                                "patch_applicator.ast_validation_warning",
                                file=clean_rel,
                                errors=val_res.errors[:2],
                            )

                    if action == "delete":
                        if os.path.exists(full_path):
                            os.remove(full_path)
                            if clean_rel not in deleted:
                                deleted.append(clean_rel)
                        continue

                    if action == "create":
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        content = str(patch.replacement or "")
                        with open(full_path, "w", encoding="utf-8") as fh:
                            fh.write(content)
                        if clean_rel not in created:
                            created.append(clean_rel)
                        if clean_rel not in touched:
                            touched.append(clean_rel)
                        continue

                    # Line-based mutations: replace, insert_before, insert_after
                    if not os.path.exists(full_path):
                        # If file doesn't exist, create it with the replacement content
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, "w", encoding="utf-8") as fh:
                            fh.write(str(patch.replacement or ""))
                        if clean_rel not in created:
                            created.append(clean_rel)
                        if clean_rel not in touched:
                            touched.append(clean_rel)
                        continue

                    with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                        lines = fh.readlines()

                    num_lines = len(lines)
                    replacement_lines = str(patch.replacement or "").splitlines(keepends=True)
                    if replacement_lines and not replacement_lines[-1].endswith("\n"):
                        replacement_lines[-1] += "\n"

                    s_line = _safe_int(patch.start_line)
                    e_line = _safe_int(patch.end_line)
                    start_idx = max(0, (s_line - 1)) if s_line is not None else 0
                    end_idx = min(num_lines, e_line) if e_line is not None else num_lines

                    if action == "replace":
                        lines[start_idx:end_idx] = replacement_lines
                    elif action == "insert_before":
                        lines[start_idx:start_idx] = replacement_lines
                    elif action == "insert_after":
                        insert_at = min(num_lines, end_idx)
                        lines[insert_at:insert_at] = replacement_lines
                    else:
                        # Fallback replace
                        lines[start_idx:end_idx] = replacement_lines

                    with open(full_path, "w", encoding="utf-8") as fh:
                        fh.writelines(lines)

                    if clean_rel not in touched:
                        touched.append(clean_rel)

            return touched, created, deleted

        except Exception as exc:
            log.error("patch_applicator.error_rolling_back", error=str(exc))
            cls.rollback(root, backups)
            raise


class BatchPlanner:
    """
    Partitions multi-file edits into topologically ordered dependency stages
    to prevent LLM output token overflow and context dispersion.
    """

    @staticmethod
    def cluster_files_into_stages(
        files: List[str],
        phases_payload: Optional[List[Dict[str, Any]]] = None,
        max_files_per_stage: int = 4,
    ) -> List[EditStage]:
        """
        Cluster files into stages based on architectural layer, or use explicit phases from Round 1.
        """
        if phases_payload and isinstance(phases_payload, list) and len(phases_payload) > 0:
            stages: List[EditStage] = []
            all_target_files: List[str] = []
            for item in phases_payload:
                if isinstance(item, dict):
                    stage_num = item.get("stage", len(stages) + 1)
                    name = item.get("name") or item.get("description") or f"Stage {stage_num}"
                    stage_files = item.get("files", [])
                    if isinstance(stage_files, list) and stage_files:
                        clean_files = [_clean_rel_path(f) for f in stage_files if _clean_rel_path(f)]
                        all_target_files.extend(clean_files)
                        stages.append(
                            EditStage(
                                stage_number=stage_num,
                                name=name,
                                target_files=clean_files,
                            )
                        )
            if stages:
                for st in stages:
                    st.reference_files = [f for f in all_target_files if f not in st.target_files]
                return stages

        clean_files = list(dict.fromkeys([_clean_rel_path(f) for f in files if _clean_rel_path(f)]))
        if len(clean_files) <= max_files_per_stage:
            return [
                EditStage(
                    stage_number=1,
                    name="Surgical Modifications",
                    target_files=clean_files,
                    reference_files=[],
                )
            ]

        layer_types: List[str] = []
        layer_domain: List[str] = []
        layer_ui: List[str] = []
        layer_tests: List[str] = []
        layer_other: List[str] = []

        for f in clean_files:
            lower = f.lower()
            if any(k in lower for k in ["/types", "types.", ".d.ts", "interface", "schema.", "migration", "/constants", "presets."]):
                layer_types.append(f)
            elif any(k in lower for k in ["/engine", "/store", "/services", "/models", "/backend", "server."]):
                layer_domain.append(f)
            elif any(k in lower for k in [".test.", ".spec.", "/tests", "test_"]):
                layer_tests.append(f)
            elif any(k in lower for k in ["/components", "/views", "/pages", "/ui", "/atoms", "exporter"]):
                layer_ui.append(f)
            else:
                layer_other.append(f)

        stages: List[EditStage] = []
        stage_idx = 1

        def _add_layer(name: str, flist: List[str]):
            nonlocal stage_idx
            for i in range(0, len(flist), max_files_per_stage):
                chunk = flist[i : i + max_files_per_stage]
                if chunk:
                    stages.append(
                        EditStage(
                            stage_number=stage_idx,
                            name=f"{name} (Part {i // max_files_per_stage + 1})" if len(flist) > max_files_per_stage else name,
                            target_files=chunk,
                            reference_files=[f for f in clean_files if f not in chunk],
                        )
                    )
                    stage_idx += 1

        if layer_types:
            _add_layer("Data Contracts, Schemas & Constants", layer_types)
        if layer_domain:
            _add_layer("Core Business Logic & Engines", layer_domain)
        if layer_ui:
            _add_layer("UI Presentation & Exporters", layer_ui)
        if layer_other:
            _add_layer("Supporting Modules & Configuration", layer_other)
        if layer_tests:
            _add_layer("Test Suites & Verification Fixtures", layer_tests)

        if not stages:
            stages.append(
                EditStage(
                    stage_number=1,
                    name="All Selected Files",
                    target_files=clean_files,
                    reference_files=[],
                )
            )

        return stages



class PatchAgent:
    """
    Two-round conversational edit agent.
    Round 1: File selector (minimal token footprint).
    Round 2: Patch generator (line-range structured JSON).
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        console: Optional[Console] = None,
        model: Optional[str] = None,
        indexer: Optional[ProjectIndexer] = None,
    ):
        self.provider = provider or LLMProvider()
        self.console = console
        self.model = model or settings.get_effective_model("PATCH")
        self.indexer = indexer or ProjectIndexer()

    async def run(
        self,
        instruction: str,
        project_dir: str,
        images: Optional[List[str]] = None,
        verbose: bool = False,
        confirm_command_callback: Optional[Callable[[ConsoleCommand], Coroutine[Any, Any, Tuple[bool, Optional[str]]]]] = None,
        auto_approve_commands: bool = False,
    ) -> PatchResult:
        """
        Execute precision 2-round edit conversation with optional vision images and executable console commands.
        """
        root = find_project_root(project_dir)
        index: ProjectIndex = self.indexer.build(root)
        total_cost = 0.0

        if index.total_files == 0:
            return PatchResult(
                success=False,
                edit_summary="No source files found in target directory.",
                error_message="Target directory contains no indexable files.",
            )

        if self.console:
            self.console.print(f"\n[bold cyan]⚡ Aztec Incremental Edit Engine[/bold cyan] [dim]({index.total_files} files indexed)[/dim]")

        # ----------------------------------------------------
        # ROUND 1: File Selector
        # ----------------------------------------------------
        from aztec_circle.engine.plan_manager import PlanManager
        plan_context = PlanManager.get_compact_plan_context(root)
        plan_section = f"\n{plan_context}\n" if plan_context else ""

        index_context = self.indexer.to_prompt_context(index)
        round1_system = render("edit_file_selector")
        round1_user = f"""EDIT INSTRUCTION:
{instruction}
{plan_section}
{index_context}

Which files must be read and edited to fulfill this instruction?"""

        from aztec_circle.tui.streaming_ui import SingleStreamVisualizer

        vis1 = SingleStreamVisualizer(
            console=self.console,
            title="Round 1: File Selection & Analysis",
            icon="🔍",
            show_preview=False,
        )
        try:
            with vis1:
                r1_resp: LLMResponse = await self.provider.invoke(
                    model=self.model,
                    system_prompt=round1_system,
                    user_message=round1_user,
                    images=images,
                    temperature=0.1,
                    on_chunk=vis1.on_chunk,
                )
            bm1 = BudgetManager()
            total_cost += bm1.record(
                input_tokens=r1_resp.prompt_tokens,
                output_tokens=r1_resp.completion_tokens,
                total_tokens=r1_resp.total_tokens,
                cached_tokens=r1_resp.cached_tokens,
            )
            r1_data = extract_json_payload(r1_resp.content)
            files_to_read = r1_data.get("files_to_read", [])
            phases_data = r1_data.get("phases", [])

            if not isinstance(files_to_read, list) or not files_to_read:
                # Fallback: select top matching files or src/App.tsx
                files_to_read = [f.rel_path for f in index.file_indices[:3] if f.rel_path.startswith("src/")]

        except Exception as exc:
            log.error("patch_agent.round1_failed", error=str(exc))
            return PatchResult(
                success=False,
                edit_summary="Failed in Round 1 file selection.",
                error_message=str(exc),
            )

        # ----------------------------------------------------
        # Validate and Normalize Files to Read
        # ----------------------------------------------------
        valid_files_to_read: List[str] = []
        for rel_file in files_to_read:
            if isinstance(rel_file, int):
                if 1 <= rel_file <= len(index.file_indices):
                    clean_rel = index.file_indices[rel_file - 1].rel_path
                else:
                    continue
            else:
                val_str = str(rel_file).strip()
                if val_str.isdigit() and 1 <= int(val_str) <= len(index.file_indices):
                    clean_rel = index.file_indices[int(val_str) - 1].rel_path
                else:
                    clean_rel = val_str.lstrip("/\\").replace("\\", "/")

            full_path = os.path.join(root, clean_rel)
            if os.path.exists(full_path) and clean_rel not in valid_files_to_read:
                valid_files_to_read.append(clean_rel)

        if not valid_files_to_read:
            valid_files_to_read = [f.rel_path for f in index.file_indices[:3] if f.rel_path.startswith("src/")]

        # ----------------------------------------------------
        # Plan Phased Execution Stages
        # ----------------------------------------------------
        stages: List[EditStage] = BatchPlanner.cluster_files_into_stages(
            files=valid_files_to_read,
            phases_payload=phases_data if isinstance(phases_data, list) else None,
        )

        if self.console:
            if len(stages) > 1:
                self.console.print(f"  [green]✓[/green] Partitioned [bold]{len(valid_files_to_read)}[/bold] file(s) into [bold cyan]{len(stages)}[/bold cyan] phased edit stages:")
                for st in stages:
                    self.console.print(f"    [dim]Stage {st.stage_number}: {st.name} ({len(st.target_files)} target files)[/dim]")
            else:
                self.console.print(f"  [green]✓[/green] Selected [bold]{len(valid_files_to_read)}[/bold] file(s) for modification: [dim]{', '.join(valid_files_to_read)}[/dim]")

        # ----------------------------------------------------
        # Multi-Stage Execution Pipeline
        # ----------------------------------------------------
        from aztec_circle.engine.project_runner import ProjectRunner
        runner = ProjectRunner(console=self.console)

        all_backups: Dict[str, Optional[str]] = {}
        all_patches: List[FilePatch] = []
        all_commands: List[ConsoleCommand] = []
        all_executed_commands: List[CommandExecutionResult] = []
        all_touched: List[str] = []
        all_created: List[str] = []
        all_deleted: List[str] = []
        stage_summaries: List[str] = []
        round2_total_tokens = 0

        async def _execute_single_cmd(cmd_obj: ConsoleCommand) -> CommandExecutionResult:
            confirmed = True
            effective_cmd = cmd_obj.command

            if confirm_command_callback is not None and not auto_approve_commands:
                confirmed, edited_cmd = await confirm_command_callback(cmd_obj)
                if edited_cmd:
                    effective_cmd = edited_cmd

            if not confirmed:
                if self.console:
                    self.console.print(f"  [yellow]⚡ Skipped console command:[/yellow] [dim]{cmd_obj.command}[/dim]")
                return CommandExecutionResult(
                    command=cmd_obj.command,
                    description=cmd_obj.description,
                    success=True,
                    confirmed=False,
                    skipped=True,
                )

            cwd_target = cmd_obj.cwd or root
            res = await runner.run_shell_command_streamed(
                cmd_str=effective_cmd,
                cwd=cwd_target,
                title=f"Command ({cmd_obj.description or 'Console'})",
            )
            return CommandExecutionResult(
                command=effective_cmd,
                description=cmd_obj.description,
                success=res.success,
                stdout=res.stdout,
                stderr=res.stderr,
                exit_code=res.exit_code,
                duration_seconds=res.duration_seconds,
                confirmed=True,
                skipped=False,
            )

        round2_system = render("edit_patch_generator")

        try:
            for stage in stages:
                stage_title = f"Round 2: Patch Generator [{stage.stage_number}/{len(stages)} - {stage.name}]" if len(stages) > 1 else "Round 2: Patch Generator & Command Proposer"

                # Generate Level-of-Detail source context (Target files full lines + Sibling files AST skeletons)
                files_block = self.indexer.get_context_with_lod(
                    project_root=root,
                    target_files=stage.target_files,
                    reference_files=stage.reference_files,
                )
                if not files_block.strip():
                    files_block = "(No existing files selected for this stage; create new files if required)"

                stage_context_note = f"\nACTIVE EDIT STAGE {stage.stage_number}/{len(stages)}: {stage.name}\n" if len(stages) > 1 else ""

                round2_user = f"""EDIT INSTRUCTION:
{instruction}
{plan_section}{stage_context_note}
SOURCE CODE & CONTEXT (NUMBERED TARGETS & AST SKELETONS):
{files_block}

Please generate the minimal, atomic JSON patches for this stage and any required console/database commands."""

                vis2 = SingleStreamVisualizer(
                    console=self.console,
                    title=stage_title,
                    icon="⚡",
                    show_preview=True,
                )

                with vis2:
                    r2_resp: LLMResponse = await self.provider.invoke(
                        model=self.model,
                        system_prompt=round2_system,
                        user_message=round2_user,
                        images=images,
                        temperature=0.1,
                        on_chunk=vis2.on_chunk,
                    )

                bm2 = BudgetManager()
                total_cost += bm2.record(
                    input_tokens=r2_resp.prompt_tokens,
                    output_tokens=r2_resp.completion_tokens,
                    total_tokens=r2_resp.total_tokens,
                    cached_tokens=r2_resp.cached_tokens,
                )
                round2_total_tokens += r2_resp.total_tokens

                r2_data = extract_json_payload(r2_resp.content)
                edit_summary = r2_data.get("edit_summary", f"Applied {stage.name} modifications.")
                stage_summaries.append(edit_summary)

                raw_patches = r2_data.get("patches", [])
                raw_commands = r2_data.get("commands", [])

                def _resolve_patch_file(raw_val: Any) -> str:
                    if raw_val is None:
                        return ""
                    if isinstance(raw_val, int):
                        if 1 <= raw_val <= len(stage.target_files):
                            return stage.target_files[raw_val - 1]
                        elif 1 <= raw_val <= len(valid_files_to_read):
                            return valid_files_to_read[raw_val - 1]
                        elif 1 <= raw_val <= len(index.file_indices):
                            return index.file_indices[raw_val - 1].rel_path
                    val_str = str(raw_val).strip()
                    if val_str.isdigit():
                        num = int(val_str)
                        if 1 <= num <= len(stage.target_files):
                            return stage.target_files[num - 1]
                        elif 1 <= num <= len(valid_files_to_read):
                            return valid_files_to_read[num - 1]
                        elif 1 <= num <= len(index.file_indices):
                            return index.file_indices[num - 1].rel_path
                    return val_str.lstrip("/\\").replace("\\", "/")

                stage_patches: List[FilePatch] = []
                for p in raw_patches:
                    if isinstance(p, dict) and "file" in p:
                        resolved_file = _resolve_patch_file(p["file"])
                        stage_patches.append(
                            FilePatch(
                                file=resolved_file,
                                action=str(p.get("action", "replace")),
                                start_line=_safe_int(p.get("start_line")),
                                end_line=_safe_int(p.get("end_line")),
                                replacement=str(p.get("replacement") or ""),
                                concern=str(p.get("concern", "Code edit")),
                            )
                        )

                if not stage_patches:
                    items = r2_data.get("items", []) if isinstance(r2_data, dict) else (r2_data if isinstance(r2_data, list) else [])
                    for p in items:
                        if isinstance(p, dict) and "file" in p:
                            resolved_file = _resolve_patch_file(p["file"])
                            stage_patches.append(
                                FilePatch(
                                    file=resolved_file,
                                    action=str(p.get("action", "replace")),
                                    start_line=_safe_int(p.get("start_line")),
                                    end_line=_safe_int(p.get("end_line")),
                                    replacement=str(p.get("replacement") or ""),
                                    concern=str(p.get("concern", "Code edit")),
                                )
                            )

                # Parse stage commands
                stage_commands: List[ConsoleCommand] = []
                if isinstance(raw_commands, list):
                    for cmd_item in raw_commands:
                        if isinstance(cmd_item, dict) and "command" in cmd_item:
                            cmd_str = str(cmd_item["command"]).strip()
                            if cmd_str:
                                stage_commands.append(
                                    ConsoleCommand(
                                        command=cmd_str,
                                        description=str(cmd_item.get("description", "Execute console command")).strip(),
                                        stage=str(cmd_item.get("stage", "post_patch")).strip(),
                                        cwd=cmd_item.get("cwd"),
                                    )
                                )
                        elif isinstance(cmd_item, str) and cmd_item.strip():
                            stage_commands.append(
                                ConsoleCommand(
                                    command=cmd_item.strip(),
                                    description="Execute console command",
                                    stage="post_patch",
                                )
                            )

                # 1. Execute Pre-Patch Commands for this stage
                pre_cmds = [c for c in stage_commands if c.stage == "pre_patch"]
                for c in pre_cmds:
                    cmd_res = await _execute_single_cmd(c)
                    all_executed_commands.append(cmd_res)

                # 2. Apply Stage File Patches Atomically (tracking all backups for global rollback)
                if stage_patches:
                    s_touched, s_created, s_deleted = PatchApplicator.apply(
                        project_root=root,
                        patches=stage_patches,
                        existing_backups=all_backups,
                    )
                    for t in s_touched:
                        if t not in all_touched:
                            all_touched.append(t)
                    for cr in s_created:
                        if cr not in all_created:
                            all_created.append(cr)
                    for d in s_deleted:
                        if d not in all_deleted:
                            all_deleted.append(d)

                    if self.console:
                        for p in stage_patches:
                            line_info = f" (L{p.start_line}-L{p.end_line})" if p.start_line is not None else ""
                            self.console.print(f"    [bold cyan]●[/bold cyan] {p.file}{line_info}: [dim]{p.concern}[/dim]")
                        self.console.print(f"  [bold green]✓ Stage {stage.stage_number} applied {len(stage_patches)} atomic patch(es)![/bold green]")

                # 3. Execute Post-Patch Commands for this stage
                post_cmds = [c for c in stage_commands if c.stage != "pre_patch"]
                for c in post_cmds:
                    cmd_res = await _execute_single_cmd(c)
                    all_executed_commands.append(cmd_res)

                all_patches.extend(stage_patches)
                all_commands.extend(stage_commands)

            if not all_patches and not all_commands:
                return PatchResult(
                    success=False,
                    edit_summary="No valid patches or commands returned by generator across all stages.",
                    round1_tokens=r1_resp.total_tokens,
                    round2_tokens=round2_total_tokens,
                    total_cost_usd=round(total_cost, 6),
                    error_message="LLM output did not include actionable patches or commands.",
                )

            if self.console and verbose:
                self.console.print(f"  [dim]Telemetry: Round 1: {r1_resp.total_tokens:,} tok | Round 2 (Total): {round2_total_tokens:,} tok | Total Cost: ${total_cost:.4f}[/dim]\n")

            # Update Living Project Plan (AZTEC_PLAN.md)
            applied_files = list(dict.fromkeys([p.file for p in all_patches]))
            run_cmd_strings = [c.command for c in all_executed_commands if not c.skipped]
            PlanManager.record_edit_iteration(
                output_dir=root,
                instruction=instruction,
                modified_files=applied_files,
                executed_commands=run_cmd_strings,
            )

            consolidated_summary = " ".join(stage_summaries) if stage_summaries else "Applied code modifications."

            return PatchResult(
                success=True,
                edit_summary=consolidated_summary,
                patches=all_patches,
                files_touched=all_touched,
                files_created=all_created,
                files_deleted=all_deleted,
                commands_proposed=all_commands,
                commands_executed=all_executed_commands,
                round1_tokens=r1_resp.total_tokens,
                round2_tokens=round2_total_tokens,
                total_cost_usd=round(total_cost, 6),
            )

        except Exception as exc:
            log.error("patch_agent.staged_execution_failed", error=str(exc))
            # Global rollback across all stages
            PatchApplicator.rollback(root, all_backups)
            return PatchResult(
                success=False,
                edit_summary="Failed during staged patch generation or application (all changes rolled back).",
                round1_tokens=r1_resp.total_tokens,
                round2_tokens=round2_total_tokens,
                total_cost_usd=round(total_cost, 6),
                error_message=str(exc),
            )
