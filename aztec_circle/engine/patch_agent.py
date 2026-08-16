"""
Patch Agent and Applicator for Aztec Incremental Edit Engine.
Executes precision, token-efficient 2-round code edits using atomic line-range patches.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import structlog
from rich.console import Console

from aztec_circle.adapters.llm_provider import LLMProvider, LLMResponse
from aztec_circle.agents.base import extract_json_payload
from aztec_circle.config import settings
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
    round1_tokens: int = 0
    round2_tokens: int = 0
    total_cost_usd: float = 0.0
    error_message: Optional[str] = None


class PatchApplicator:
    """
    Applies structured patches to the filesystem with full atomic rollback on error.
    """

    @staticmethod
    def apply(project_root: str, patches: List[FilePatch]) -> Tuple[List[str], List[str], List[str]]:
        """
        Apply patches atomically. Returns (files_touched, files_created, files_deleted).
        If any patch operation fails, rolls back all modified/created/deleted files.
        """
        root = find_project_root(project_root)
        backups: Dict[str, Optional[str]] = {}  # None indicates file didn't exist before
        touched: List[str] = []
        created: List[str] = []
        deleted: List[str] = []

        # 1. Capture backups of all affected files
        for patch in patches:
            clean_rel = patch.file.lstrip("/\\").replace("\\", "/")
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
            clean_rel = p.file.lstrip("/\\").replace("\\", "/")
            patches_by_file.setdefault(clean_rel, []).append(p)

        try:
            for clean_rel, file_patches in patches_by_file.items():
                full_path = os.path.join(root, clean_rel)

                for patch in file_patches:
                    action = (patch.action or "replace").lower()

                    if action == "delete":
                        if os.path.exists(full_path):
                            os.remove(full_path)
                            if clean_rel not in deleted:
                                deleted.append(clean_rel)
                        continue

                    if action == "create":
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        content = patch.replacement or ""
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
                            fh.write(patch.replacement or "")
                        if clean_rel not in created:
                            created.append(clean_rel)
                        if clean_rel not in touched:
                            touched.append(clean_rel)
                        continue

                    with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                        lines = fh.readlines()

                    num_lines = len(lines)
                    replacement_lines = (patch.replacement or "").splitlines(keepends=True)
                    if replacement_lines and not replacement_lines[-1].endswith("\n"):
                        replacement_lines[-1] += "\n"

                    start_idx = max(0, (patch.start_line - 1)) if patch.start_line is not None else 0
                    end_idx = min(num_lines, patch.end_line) if patch.end_line is not None else num_lines

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
            # Rollback all files
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
            raise


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
    ) -> PatchResult:
        """
        Execute precision 2-round edit conversation with optional vision images.
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

        if self.console and verbose:
            self.console.print("  [dim]Round 1: Identifying relevant source files...[/dim]")

        try:
            r1_resp: LLMResponse = await self.provider.invoke(
                model=self.model,
                system_prompt=round1_system,
                user_message=round1_user,
                images=images,
                temperature=0.1,
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
        # Prepare Numbered File Contents
        # ----------------------------------------------------
        numbered_files_section = []
        valid_files_to_read = []

        for rel_file in files_to_read:
            clean_rel = rel_file.lstrip("/\\").replace("\\", "/")
            full_path = os.path.join(root, clean_rel)
            if os.path.exists(full_path):
                valid_files_to_read.append(clean_rel)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                        lines = fh.readlines()
                    numbered = "".join(f"{idx + 1:4d}: {line}" for idx, line in enumerate(lines))
                    numbered_files_section.append(f"### FILE: {clean_rel} ({len(lines)} lines)\n```\n{numbered}\n```")
                except Exception:
                    pass

        if self.console:
            self.console.print(f"  [green]✓[/green] Selected [bold]{len(valid_files_to_read)}[/bold] file(s) for modification: [dim]{', '.join(valid_files_to_read)}[/dim]")

        # ----------------------------------------------------
        # ROUND 2: Patch Generator
        # ----------------------------------------------------
        round2_system = render("edit_patch_generator")
        files_block = "\n\n".join(numbered_files_section) if numbered_files_section else "(No existing files selected; create new files if required)"

        round2_user = f"""EDIT INSTRUCTION:
{instruction}
{plan_section}
NUMBERED SOURCE FILES:
{files_block}

Please generate the minimal, atomic JSON patches to fulfill the instruction."""

        if self.console and verbose:
            self.console.print("  [dim]Round 2: Generating structured line-range patches...[/dim]")

        try:
            r2_resp: LLMResponse = await self.provider.invoke(
                model=self.model,
                system_prompt=round2_system,
                user_message=round2_user,
                images=images,
                temperature=0.1,
            )
            bm2 = BudgetManager()
            total_cost += bm2.record(
                input_tokens=r2_resp.prompt_tokens,
                output_tokens=r2_resp.completion_tokens,
                total_tokens=r2_resp.total_tokens,
                cached_tokens=r2_resp.cached_tokens,
            )
            r2_data = extract_json_payload(r2_resp.content)
            edit_summary = r2_data.get("edit_summary", "Applied code modifications.")
            raw_patches = r2_data.get("patches", [])

            patches: List[FilePatch] = []
            for p in raw_patches:
                if isinstance(p, dict) and "file" in p:
                    patches.append(
                        FilePatch(
                            file=p["file"],
                            action=p.get("action", "replace"),
                            start_line=p.get("start_line"),
                            end_line=p.get("end_line"),
                            replacement=p.get("replacement"),
                            concern=p.get("concern", "Code edit"),
                        )
                    )

            if not patches:
                # Secondary: Check if r2_data itself is a list or contains items key
                items = r2_data.get("items", []) if isinstance(r2_data, dict) else (r2_data if isinstance(r2_data, list) else [])
                for p in items:
                    if isinstance(p, dict) and "file" in p:
                        patches.append(
                            FilePatch(
                                file=p["file"],
                                action=p.get("action", "replace"),
                                start_line=p.get("start_line"),
                                end_line=p.get("end_line"),
                                replacement=p.get("replacement"),
                                concern=p.get("concern", "Code edit"),
                            )
                        )

            if not patches:
                # Tertiary Regex Fallback: Scan text for individual patch objects
                patch_matches = re.finditer(r"\{[^{}]*\"file\"[^{}]*\}", r2_resp.content, re.DOTALL)
                for pm in patch_matches:
                    try:
                        p_obj = json_repair.loads(pm.group(0))
                        if isinstance(p_obj, dict) and "file" in p_obj:
                            patches.append(
                                FilePatch(
                                    file=p_obj["file"],
                                    action=p_obj.get("action", "replace"),
                                    start_line=p_obj.get("start_line"),
                                    end_line=p_obj.get("end_line"),
                                    replacement=p_obj.get("replacement"),
                                    concern=p_obj.get("concern", "Code edit"),
                                )
                            )
                    except Exception:
                        pass

            if not patches:
                return PatchResult(
                    success=False,
                    edit_summary="No valid patches returned by generator.",
                    round1_tokens=r1_resp.total_tokens,
                    round2_tokens=r2_resp.total_tokens,
                    total_cost_usd=round(total_cost, 6),
                    error_message="LLM output did not include actionable patches.",
                )

            # ----------------------------------------------------
            # Apply Patches Atomically
            # ----------------------------------------------------
            touched, created, deleted = PatchApplicator.apply(root, patches)

            if self.console:
                for p in patches:
                    action_tag = f"[{p.action}]"
                    line_info = f" (L{p.start_line}-L{p.end_line})" if p.start_line is not None else ""
                    self.console.print(f"    [bold cyan]●[/bold cyan] {p.file}{line_info}: [dim]{p.concern}[/dim]")

                self.console.print(f"  [bold green]✓ Successfully applied {len(patches)} atomic patch(es)![/bold green]")
                if verbose:
                    self.console.print(f"  [dim]Telemetry: Round 1: {r1_resp.total_tokens:,} tok | Round 2: {r2_resp.total_tokens:,} tok | Total Cost: ${total_cost:.4f}[/dim]\n")

            # Update Living Project Plan (AZTEC_PLAN.md)
            applied_files = [p.file for p in patches]
            PlanManager.record_edit_iteration(output_dir=root, instruction=instruction, modified_files=applied_files)

            return PatchResult(
                success=True,
                edit_summary=edit_summary,
                patches=patches,
                files_touched=touched,
                files_created=created,
                files_deleted=deleted,
                round1_tokens=r1_resp.total_tokens,
                round2_tokens=r2_resp.total_tokens,
                total_cost_usd=round(total_cost, 6),
            )

        except Exception as exc:
            log.error("patch_agent.round2_or_apply_failed", error=str(exc))
            return PatchResult(
                success=False,
                edit_summary="Failed to apply generated patches.",
                round1_tokens=r1_resp.total_tokens,
                total_cost_usd=round(total_cost, 6),
                error_message=str(exc),
            )
