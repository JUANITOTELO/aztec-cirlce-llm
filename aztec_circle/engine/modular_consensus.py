"""
Modular Edit Consensus Engine for Aztec Decision Circle.
Executes multi-generational consensus debates specifically focused on adding
new modules, major features, and architectural extensions to existing projects.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple
import structlog
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from aztec_circle.adapters.llm_provider import LLMProvider, LLMResponse
from aztec_circle.agents.base import extract_json_payload
from aztec_circle.config import settings
from aztec_circle.domain.exceptions import BudgetExceeded, YouthOverrideHalt
from aztec_circle.domain.models import (
    AgentRank,
    CirclePhase,
    CommandExecutionResult,
    ConsoleCommand,
    ElderAuditItem,
    ElderVerdict,
    FallbackPolicy,
    ModularDraftOutput,
    ModularPatchItem,
    SeverityLevel,
    VerdictStatus,
    YouthBrainstormOutput,
    YouthRiskItem,
)
from aztec_circle.engine.budget_manager import BudgetManager
from aztec_circle.engine.build_fixer import BuildFixAgent
from aztec_circle.engine.consensus import ConsensusEngine
from aztec_circle.engine.integration_enforcer import enforce_mandatory_patches
from aztec_circle.engine.linking_engine import (
    DependencyGraph,
    IntegrationManifest,
    LinkingEngine,
    load_project_aztec_config,
)
from aztec_circle.engine.patch_agent import FilePatch, PatchApplicator
from aztec_circle.engine.plan_manager import PlanManager
from aztec_circle.engine.post_apply_verifier import PostApplyVerifier, VerificationResult
from aztec_circle.engine.project_indexer import ProjectIndex, ProjectIndexer
from aztec_circle.engine.project_runner import ProjectRunner
from aztec_circle.engine.scaffolder import find_project_root
from aztec_circle.prompts import render

log = structlog.get_logger(__name__)


@dataclass
class ModularConsensusResult:
    """Outcome of an edit-focused modular consensus debate."""
    success: bool
    goal: str
    architecture_overview: str
    new_files: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    deleted_files: List[str] = field(default_factory=list)
    commands_executed: List[CommandExecutionResult] = field(default_factory=list)
    mitigations_applied: List[str] = field(default_factory=list)
    loop_count: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    verdict: Optional[ElderVerdict] = None
    error_message: Optional[str] = None
    verification_passed: bool = True


class ModularConsensusOrchestrator:
    """
    Orchestrates contextual, multi-generational debate cycles for adding
    new modules and features to an existing project.
    """

    def __init__(
        self,
        project_dir: str,
        goal: str,
        images: Optional[List[str]] = None,
        provider: Optional[LLMProvider] = None,
        console: Optional[Console] = None,
        budget_limit_usd: float = 1.00,
        max_loops: int = 2,
        event_queue: Optional[asyncio.Queue] = None,
    ):
        self.root = find_project_root(project_dir) or project_dir
        self.goal = goal
        self.images = images or []
        self.provider = provider or LLMProvider()
        self.console = console
        self.budget = BudgetManager(limit_usd=budget_limit_usd)
        self.max_loops = max_loops
        self.events = event_queue or asyncio.Queue()
        self.consensus_engine = ConsensusEngine()
        self.indexer = ProjectIndexer()
        self.aztec_config = load_project_aztec_config(self.root)
        self.linking_engine = LinkingEngine(
            config_overrides=self.aztec_config.get("entry_point_overrides", {})
        )
        self._integration_manifest: Optional[IntegrationManifest] = None

        # Model bindings
        self.youth_chaos_model = settings.get_effective_model("YOUTH_CHAOS")
        self.youth_advocate_model = settings.get_effective_model("YOUTH_ADVOCATE")
        self.peer_model = settings.get_effective_model("PEER")
        self.elder_security_model = settings.get_effective_model("ELDER_SECURITY")
        self.elder_structural_model = settings.get_effective_model("ELDER_STRUCTURAL")

    async def _emit(self, event_name: str, payload: Dict[str, Any]) -> None:
        try:
            await self.events.put({"event": event_name, **payload})
        except Exception:
            pass

    def _build_codebase_context(self) -> str:
        """Extract compact, token-efficient summary of the current codebase and dynamic dependency graph."""
        index: ProjectIndex = self.indexer.build(self.root)
        index_summary = self.indexer.to_prompt_context(index)
        plan_summary = PlanManager.get_compact_plan_context(self.root) or "No prior AZTEC_PLAN.md found."

        # Build dynamic dependency graph and integration manifest
        graph: DependencyGraph = self.linking_engine.build_graph(self.root)
        extra_keys = self.aztec_config.get("extra_key_files", [])
        self._integration_manifest = self.linking_engine.build_integration_manifest(
            graph=graph,
            goal=self.goal,
            extra_key_files=extra_keys,
        )
        linking_context = self.linking_engine.to_prompt_context(self._integration_manifest)

        # Sample key existing schema / router / coordinator files dynamically
        key_files_snippets = []
        sampled_targets: List[str] = list(
            dict.fromkeys(
                list(self._integration_manifest.entry_points.keys())
                + self._integration_manifest.mandatory_patch_targets
                + self._integration_manifest.hotspot_files
                + extra_keys
            )
        )

        for rel in sampled_targets[:12]:
            fp = os.path.join(self.root, rel)
            if os.path.exists(fp) and os.path.isfile(fp):
                try:
                    with open(fp, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    lines = content.splitlines()
                    # Include first 120 lines if long
                    snippet = "\n".join(lines[:120])
                    key_files_snippets.append(f"### CURRENT {rel} ({len(lines)} lines):\n```\n{snippet}\n```")
                except Exception:
                    pass

        key_files_text = "\n\n".join(key_files_snippets) if key_files_snippets else "No anchor files found on disk."

        return f"""=== EXISTING CODEBASE BLUEPRINT ===
{plan_summary}

=== EXISTING PROJECT FILE TREE ===
{index_summary}

=== DEPENDENCY GRAPH & MANDATORY INTEGRATION TARGETS ===
{linking_context}

=== KEY ARCHITECTURAL ANCHORS ===
{key_files_text}"""

    async def run(
        self,
        confirm_command_callback: Optional[Callable[[ConsoleCommand], Coroutine[Any, Any, Tuple[bool, Optional[str]]]]] = None,
        auto_approve_commands: bool = False,
        verbose: bool = True,
    ) -> ModularConsensusResult:
        """
        Execute full modular consensus cycle: Youth Brainstorm -> Peer Drafting -> Elder Audits -> Application.
        """
        log.info("modular_consensus.started", goal=self.goal, root=self.root)
        total_tokens = 0
        total_cost = 0.0

        codebase_context = self._build_codebase_context()

        # ----------------------------------------------------
        # PHASE 1: Youth Modular Brainstorming (Parallel)
        # ----------------------------------------------------
        await self._emit("PHASE_START", {"phase": "YOUTH_BRAINSTORM"})
        if self.console:
            self.console.rule("[bold yellow]🧠 Youth Rank Modular Brainstorming (Chaos & Devil's Advocate)[/bold yellow]", style="yellow")

        youth_system = render("youth_modular_brainstorm")
        youth_user = f"""NEW MODULE / FEATURE GOAL:
{self.goal}

{codebase_context}

Analyze this goal against the existing codebase. Identify radical opportunities, architecture risks, and integration edge cases."""

        from aztec_circle.tui.streaming_ui import ParallelStreamVisualizer, SingleStreamVisualizer

        youth_vis = ParallelStreamVisualizer(
            console=self.console,
            title="Youth Rank Parallel Brainstorming",
            icon="🧠",
            border_style="yellow",
        )
        on_chunk_chaos = youth_vis.register_agent("chaos", "Chaos Brainstormer", icon="🌀")
        on_chunk_advocate = youth_vis.register_agent("advocate", "Devil's Advocate", icon="🛡")

        with youth_vis:
            youth_tasks = [
                self.provider.invoke(
                    model=self.youth_chaos_model,
                    system_prompt=youth_system,
                    user_message=f"[CHAOS BRAINSTORMER]\n{youth_user}",
                    images=self.images,
                    temperature=0.9,
                    on_chunk=on_chunk_chaos,
                ),
                self.provider.invoke(
                    model=self.youth_advocate_model,
                    system_prompt=youth_system,
                    user_message=f"[DEVIL'S ADVOCATE]\n{youth_user}",
                    images=self.images,
                    temperature=0.8,
                    on_chunk=on_chunk_advocate,
                ),
            ]
            youth_resps = await asyncio.gather(*youth_tasks, return_exceptions=True)
        youth_outputs: List[YouthBrainstormOutput] = []

        for idx, resp in enumerate(youth_resps):
            if isinstance(resp, Exception):
                log.error("modular_consensus.youth_failed", error=str(resp))
                continue

            total_tokens += resp.total_tokens
            total_cost += self.budget.record(
                input_tokens=resp.prompt_tokens,
                output_tokens=resp.completion_tokens,
                total_tokens=resp.total_tokens,
                cached_tokens=resp.cached_tokens,
            )
            data = extract_json_payload(resp.content)
            persona_name = "chaos_brainstormer" if idx == 0 else "devils_advocate"

            risks = []
            for r in data.get("identified_risks", []):
                if isinstance(r, dict):
                    sev = r.get("severity", "MEDIUM")
                    if sev not in SeverityLevel.__members__:
                        sev = "MEDIUM"
                    risks.append(
                        YouthRiskItem(
                            category=r.get("category", "Integration"),
                            description=r.get("description", "Identified risk"),
                            severity=SeverityLevel(sev),
                            suggested_mitigation=r.get("suggested_mitigation", "Address in architecture"),
                            is_showstopper=bool(r.get("is_showstopper", False)),
                        )
                    )

            yo = YouthBrainstormOutput(
                agent_id=f"youth_{persona_name}",
                persona=persona_name,
                radical_ideas=data.get("radical_ideas", []),
                identified_risks=risks,
                adversarial_scenarios=data.get("adversarial_scenarios", []),
                override_triggered=bool(data.get("override_triggered", False)),
                override_rationale=data.get("override_rationale"),
                tokens_used=resp.total_tokens,
            )
            youth_outputs.append(yo)

            if self.console:
                agent_label = "Chaos Brainstormer" if idx == 0 else "Devil's Advocate"
                self.console.print(f"  [green]✓[/green] [bold]{agent_label}[/bold] identified [bold]{len(risks)}[/bold] integration risk(s) and [bold]{len(yo.radical_ideas)}[/bold] feature idea(s)")

        # Check safety override
        showstoppers = [r for yo in youth_outputs for r in yo.identified_risks if r.is_showstopper]
        overrides = [yo for yo in youth_outputs if yo.override_triggered]
        if showstoppers or overrides:
            msg = "Critical showstopper flagged by Youth safety gate."
            if self.console:
                self.console.print(f"[bold red]🛑 Emergency Halt:[/bold red] {msg}")
            return ModularConsensusResult(
                success=False,
                goal=self.goal,
                architecture_overview="Halted by safety gate",
                error_message=msg,
            )

        # ----------------------------------------------------
        # PHASES 2, 3, 4: Peer Drafting & Elder Audit Consensus Loops
        # ----------------------------------------------------
        elder_rework_instructions: Optional[str] = None
        loop_count = 0
        final_draft: Optional[ModularDraftOutput] = None
        last_verdict: Optional[ElderVerdict] = None

        formatted_risks = []
        for yo in youth_outputs:
            for r in yo.identified_risks:
                formatted_risks.append(f"- [{r.severity.value}] ({r.category}) {r.description} ➔ Mitigation: {r.suggested_mitigation}")
        risk_block = "\n".join(formatted_risks) if formatted_risks else "None identified."

        while loop_count <= self.max_loops:
            await self._emit("PHASE_START", {"phase": "PEER_DRAFTING", "loop": loop_count})
            if self.console:
                self.console.print()
                self.console.rule(f"[bold blue]⚙  Peer Modular Architect Drafting (Loop {loop_count})[/bold blue]", style="blue")

            peer_system = render("peer_modular_drafter")
            peer_user_parts = [
                f"NEW MODULE / FEATURE GOAL:\n{self.goal}\n",
                f"YOUTH ADVERSARIAL RISK LOG:\n{risk_block}\n",
                f"{codebase_context}\n",
            ]

            if self._integration_manifest and self._integration_manifest.mandatory_patch_targets:
                mandatory_str = "\n".join(f"  - {t}" for t in self._integration_manifest.mandatory_patch_targets)
                peer_user_parts.append(
                    f"⚠️ MANDATORY INTEGRATION DIRECTIVE:\n"
                    f"You MUST include surgical patch entries in the 'patches' array for the relevant coordinator files:\n{mandatory_str}\n"
                    f"Do not create isolated modules that are not wired into these existing coordinators.\n"
                )

            if loop_count > 0 and elder_rework_instructions:
                flaw_summary = "\n".join(f"  - {f}" for f in (last_verdict.critical_flaws if last_verdict else []))
                flaws_block = f"ELDER COUNCIL REJECTION — LOOP {loop_count} FLAWS (Fix ALL of these):\n{flaw_summary}\n\n" if flaw_summary else ""
                peer_user_parts.append(
                    f"{flaws_block}"
                    f"REQUIRED ACTIONS:\n{elder_rework_instructions}\n"
                    f"CRITICAL: Fix the `new_files` keys — every key must be a valid path like `src/types/category.ts`.\n"
                )

            peer_user_parts.append("Synthesize complete, production-ready new files and surgical patches to integrate this module seamlessly.")
            peer_user = "\n".join(peer_user_parts)

            peer_vis = SingleStreamVisualizer(
                console=self.console,
                title=f"Peer Modular Architect Drafting (Loop {loop_count})",
                icon="⚙",
                show_preview=True,
            )

            with peer_vis:
                peer_resp = await self.provider.invoke(
                    model=self.peer_model,
                    system_prompt=peer_system,
                    user_message=peer_user,
                    images=self.images,
                    temperature=0.25,
                    on_chunk=peer_vis.on_chunk,
                )

            total_tokens += peer_resp.total_tokens
            total_cost += self.budget.record(
                input_tokens=peer_resp.prompt_tokens,
                output_tokens=peer_resp.completion_tokens,
                total_tokens=peer_resp.total_tokens,
                cached_tokens=peer_resp.cached_tokens,
            )

            peer_data = extract_json_payload(peer_resp.content)
            new_files_map = peer_data.get("new_files", {})
            if not isinstance(new_files_map, dict):
                new_files_map = {}

            raw_patches = peer_data.get("patches", [])
            parsed_patches: List[ModularPatchItem] = []
            if isinstance(raw_patches, list):
                for p in raw_patches:
                    if isinstance(p, dict) and "file" in p:
                        parsed_patches.append(
                            ModularPatchItem(
                                file=p["file"],
                                action=p.get("action", "replace"),
                                start_line=p.get("start_line"),
                                end_line=p.get("end_line"),
                                replacement=p.get("replacement"),
                                concern=p.get("concern", "Module integration patch"),
                            )
                        )

            raw_commands = peer_data.get("commands", [])
            parsed_commands: List[ConsoleCommand] = []
            if isinstance(raw_commands, list):
                for c in raw_commands:
                    if isinstance(c, dict) and "command" in c:
                        parsed_commands.append(
                            ConsoleCommand(
                                command=str(c["command"]).strip(),
                                description=str(c.get("description", "Execute console command")).strip(),
                                stage=str(c.get("stage", "post_patch")).strip(),
                                cwd=c.get("cwd"),
                            )
                        )
                    elif isinstance(c, str) and c.strip():
                        parsed_commands.append(ConsoleCommand(command=c.strip()))

            draft = ModularDraftOutput(
                agent_id="peer_modular_architect",
                loop_index=loop_count,
                architecture_overview=peer_data.get("architecture_overview", "Modular architecture synthesized."),
                new_files=new_files_map,
                patches=parsed_patches,
                commands=parsed_commands,
                mitigations_applied=peer_data.get("mitigations_applied", []),
                assumptions_made=peer_data.get("assumptions_made", []),
                tokens_used=peer_resp.total_tokens,
            )
            final_draft = draft

            if self.console:
                self.console.print(f"  [green]✓[/green] [bold]Peer Architect[/bold] synthesized [bold]{len(new_files_map)}[/bold] new file(s), [bold]{len(parsed_patches)}[/bold] patch(es), and [bold]{len(parsed_commands)}[/bold] command(s)")

            # ----------------------------------------------------
            # PHASE 3: Elder Council Modular Audits (Parallel)
            # ----------------------------------------------------
            await self._emit("PHASE_START", {"phase": "ELDER_AUDIT", "loop": loop_count})
            if self.console:
                self.console.print()
                self.console.rule(f"[bold magenta]👁  Elder Council Modular & Security Audits (Loop {loop_count})[/bold magenta]", style="magenta")

            elder_system = render("elder_modular_audit")
            # Provide Elder with fuller file content (up to 200 lines, 4 files) for real audit
            full_excerpts = {}
            for k, v in list(draft.new_files.items())[:4]:
                if isinstance(v, str):
                    lines = v.splitlines()
                    excerpt = "\n".join(lines[:200])
                    full_excerpts[k] = excerpt + ("\n... (truncated)" if len(lines) > 200 else "")

            draft_summary_json = json.dumps({
                "architecture_overview": draft.architecture_overview,
                "new_files_created": list(draft.new_files.keys()),
                "patches_to_apply": [p.model_dump() for p in draft.patches],
                "commands_to_execute": [c.model_dump() for c in draft.commands],
                "mitigations_applied": draft.mitigations_applied,
                "new_file_content_for_audit": full_excerpts,
            }, indent=2)

            elder_user = f"""NEW MODULE GOAL:
{self.goal}

PROPOSED MODULAR DRAFT:
{draft_summary_json}

{codebase_context}

Audit this modular design for integration cohesion, security, non-skeleton delivery, type safety, and database safety."""

            elder_vis = ParallelStreamVisualizer(
                console=self.console,
                title=f"Elder Council Modular & Security Audits (Loop {loop_count})",
                icon="👁",
                border_style="magenta",
            )
            on_chunk_sec = elder_vis.register_agent("sec", "Security Auditor", icon="🔒")
            on_chunk_struct = elder_vis.register_agent("struct", "Structural Auditor", icon="🏛")

            with elder_vis:
                elder_tasks = [
                    self.provider.invoke(
                        model=self.elder_security_model,
                        system_prompt=elder_system,
                        user_message=f"[SECURITY & GOVERNANCE AUDITOR]\n{elder_user}",
                        images=self.images,
                        temperature=0.0,
                        on_chunk=on_chunk_sec,
                    ),
                    self.provider.invoke(
                        model=self.elder_structural_model,
                        system_prompt=elder_system,
                        user_message=f"[STRUCTURAL & MODULAR AUDITOR]\n{elder_user}",
                        images=self.images,
                        temperature=0.0,
                        on_chunk=on_chunk_struct,
                    ),
                ]

                elder_resps = await asyncio.gather(*elder_tasks, return_exceptions=True)
            verdicts: List[ElderVerdict] = []

            for idx, resp in enumerate(elder_resps):
                if isinstance(resp, Exception):
                    log.error("modular_consensus.elder_failed", error=str(resp))
                    continue

                total_tokens += resp.total_tokens
                total_cost += self.budget.record(
                    input_tokens=resp.prompt_tokens,
                    output_tokens=resp.completion_tokens,
                    total_tokens=resp.total_tokens,
                    cached_tokens=resp.cached_tokens,
                )
                auditor_name = "elder_security_governance" if idx == 0 else "elder_structural_perf"
                v_data = extract_json_payload(resp.content)

                audit_items = []
                for it in v_data.get("audit_items", []):
                    if isinstance(it, dict):
                        audit_items.append(
                            ElderAuditItem(
                                criterion=it.get("criterion", "Modular Standard"),
                                weight=float(it.get("weight", 0.2)),
                                score=float(it.get("score", 7.0)),
                                critique=it.get("critique", "Evaluation completed."),
                                passed=bool(it.get("passed", True)),
                            )
                        )

                flaws = v_data.get("critical_flaws", [])
                if not isinstance(flaws, list):
                    flaws = [str(flaws)] if flaws else []

                score_val = float(v_data.get("weighted_score", 8.0))
                status_enum = VerdictStatus.APPROVED if (score_val >= 8.0 and not flaws) else VerdictStatus.REJECTED

                verd = ElderVerdict(
                    agent_id=auditor_name,
                    persona="security" if idx == 0 else "structural",
                    status=status_enum,
                    weighted_score=score_val,
                    audit_items=audit_items,
                    critical_flaws=flaws,
                    reworking_instructions=v_data.get("reworking_instructions"),
                    tokens_used=resp.total_tokens,
                )
                verdicts.append(verd)

                if self.console:
                    auditor_label = "Security Auditor" if idx == 0 else "Structural Auditor"
                    status_badge = "[bold green]APPROVED[/bold green]" if verd.status == VerdictStatus.APPROVED else "[bold red]REJECTED[/bold red]"
                    self.console.print(f"  [magenta]👁[/magenta] [bold]{auditor_label}[/bold] Score: [bold]{verd.weighted_score:.1f}/10.0[/bold] ➔ {status_badge}")

            # ----------------------------------------------------
            # PHASE 4: Linking Enforcement & Consensus Arbitration
            # ----------------------------------------------------
            if self._integration_manifest:
                missing_flaws = enforce_mandatory_patches(
                    manifest=self._integration_manifest,
                    new_files=draft.new_files,
                    patches=draft.patches,
                )
                if missing_flaws:
                    log.warning("modular_consensus.mandatory_patches_missing", count=len(missing_flaws))
                    for verd in verdicts:
                        verd.critical_flaws.extend(missing_flaws)
                        verd.status = VerdictStatus.REJECTED
                        if verd.weighted_score > 6.5:
                            verd.weighted_score = 6.5

            consolidated = self.consensus_engine.arbitrate(verdicts)
            last_verdict = consolidated

            if self.console:
                status_txt = "[bold green]CONSENSUS APPROVED[/bold green]" if consolidated.status == VerdictStatus.APPROVED else "[bold yellow]ITERATING REVISION LOOP[/bold yellow]"
                self.console.print(f"  [bold cyan]⚖  Consensus Arbitration:[/bold cyan] Weighted Score: [bold]{consolidated.weighted_score:.2f}/10.0[/bold] ➔ {status_txt}")

            if consolidated.status == VerdictStatus.APPROVED:
                break

            if loop_count >= self.max_loops:
                if self.console:
                    self.console.print(f"\n[yellow]Reached max debate loops ({self.max_loops}). Releasing best-effort modular draft with Elder mitigations.[/yellow]")
                break

            elder_rework_instructions = consolidated.reworking_instructions or "Address all identified critical flaws and modular integrity requirements."
            loop_count += 1

        if not final_draft:
            return ModularConsensusResult(
                success=False,
                goal=self.goal,
                architecture_overview="Failed to generate modular draft",
                error_message="No draft generated during consensus debate.",
            )

        # ----------------------------------------------------
        # PHASE 5: Application & Verification
        # ----------------------------------------------------
        if self.console:
            self.console.print()
            self.console.rule("[bold green]🏁 Applying Consensus-Approved Modular Deliverable[/bold green]", style="green")

        touched_files: List[str] = []
        created_files: List[str] = []
        deleted_files: List[str] = []
        executed_commands: List[CommandExecutionResult] = []

        runner = ProjectRunner(console=self.console)

        # Helper to execute command with confirmation
        async def _run_command(cmd_obj: ConsoleCommand) -> CommandExecutionResult:
            confirmed = True
            effective_cmd = cmd_obj.command

            if confirm_command_callback is not None and not auto_approve_commands:
                confirmed, edited_cmd = await confirm_command_callback(cmd_obj)
                if edited_cmd:
                    effective_cmd = edited_cmd

            if not confirmed:
                if self.console:
                    self.console.print(f"  [yellow]⚡ Skipped command:[/yellow] [dim]{cmd_obj.command}[/dim]")
                return CommandExecutionResult(
                    command=cmd_obj.command,
                    description=cmd_obj.description,
                    success=True,
                    confirmed=False,
                    skipped=True,
                )

            res = await runner.run_shell_command_streamed(
                cmd_str=effective_cmd,
                cwd=cmd_obj.cwd or self.root,
                title=f"Command ({cmd_obj.description or 'Modular Setup'})",
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

        # 1. Execute Pre-Patch Commands
        for c in [cmd for cmd in final_draft.commands if cmd.stage == "pre_patch"]:
            c_res = await _run_command(c)
            executed_commands.append(c_res)

        # 2. Write New Files to Disk (with path validation)
        VALID_EXTENSIONS = {
            ".ts", ".tsx", ".js", ".jsx", ".css", ".html",
            ".json", ".py", ".php", ".sql", ".md", ".lean",
        }
        for rel_path, content in final_draft.new_files.items():
            clean_rel = rel_path.lstrip("/\\").replace("\\", "/")
            # Validate: must look like a file path with slash or recognized extension
            _, ext = os.path.splitext(clean_rel)
            if ("/" not in clean_rel and "\\" not in clean_rel) or ext.lower() not in VALID_EXTENSIONS:
                log.warning(
                    "modular_consensus.invalid_new_file_key_skipped",
                    key=clean_rel,
                    reason="Not a valid relative file path",
                )
                if self.console:
                    self.console.print(f"    [bold yellow]⚠ Skipped invalid new_file key:[/bold yellow] [dim]{clean_rel!r}[/dim] (not a valid path)")
                continue
            full_path = os.path.join(self.root, clean_rel)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            created_files.append(clean_rel)
            if self.console:
                self.console.print(f"    [bold green]★ Created:[/bold green] {clean_rel}")

        # 3. Apply File Patches
        patches_to_apply = [
            FilePatch(
                file=p.file,
                action=p.action,
                start_line=p.start_line,
                end_line=p.end_line,
                replacement=p.replacement,
                concern=p.concern,
            )
            for p in final_draft.patches
        ]
        if patches_to_apply:
            t, c, d = PatchApplicator.apply(self.root, patches_to_apply)
            touched_files.extend(t)
            created_files.extend(c)
            deleted_files.extend(d)
            if self.console:
                for p in patches_to_apply:
                    line_info = f" (L{p.start_line}-L{p.end_line})" if p.start_line is not None else ""
                    self.console.print(f"    [bold cyan]● Patched:[/bold cyan] {p.file}{line_info}: [dim]{p.concern}[/dim]")

        # 4. Execute Post-Patch Commands
        for c in [cmd for cmd in final_draft.commands if cmd.stage != "pre_patch"]:
            c_res = await _run_command(c)
            executed_commands.append(c_res)

        # 5. Post-Apply Verification & Self-Healing
        verifier = PostApplyVerifier(project_root=self.root, console=self.console, runner=runner)
        custom_verif_cmd = self.aztec_config.get("verifier_command")
        verif_result: VerificationResult = await verifier.verify(custom_command=custom_verif_cmd)

        verification_passed = verif_result.success
        if not verif_result.success and verif_result.command_result:
            if self.console:
                self.console.print(f"\n[bold yellow]⚠ Post-Apply Verification found {verif_result.error_count} diagnostic issue(s). Initiating auto-healing...[/bold yellow]")
            try:
                fix_agent = BuildFixAgent(
                    provider=self.provider,
                    console=self.console,
                    max_iterations=2,
                )
                fix_res = await fix_agent.fix(
                    project_dir=self.root,
                    initial_build_result=verif_result.command_result,
                    runner=runner,
                )
                if fix_res.patches_applied:
                    for patched_file in fix_res.patches_applied:
                        if patched_file not in touched_files:
                            touched_files.append(patched_file)
                verification_passed = fix_res.success
            except Exception as fix_err:
                log.warning("modular_consensus.auto_healing_failed", error=str(fix_err))

        # 6. Update Living Project Blueprint (AZTEC_PLAN.md)
        all_affected = list(dict.fromkeys(created_files + touched_files))
        cmd_strings = [c.command for c in executed_commands if not c.skipped]
        PlanManager.record_edit_iteration(
            output_dir=self.root,
            instruction=f"Module Consensus: {self.goal}",
            modified_files=all_affected,
            executed_commands=cmd_strings,
        )

        if self.console:
            self.console.print(f"\n[bold green]✓ Modular Consensus Successfully Applied![/bold green] ([bold]{len(created_files)}[/bold] created, [bold]{len(touched_files)}[/bold] patched)")
            if verbose:
                self.console.print(f"[dim]Telemetry: {total_tokens:,} tokens consumed | Cost: ${total_cost:.4f} | Loops: {loop_count}[/dim]\n")

        return ModularConsensusResult(
            success=True,
            goal=self.goal,
            architecture_overview=final_draft.architecture_overview,
            new_files=created_files,
            modified_files=touched_files,
            deleted_files=deleted_files,
            commands_executed=executed_commands,
            mitigations_applied=final_draft.mitigations_applied,
            loop_count=loop_count,
            total_tokens_used=total_tokens,
            total_cost_usd=round(total_cost, 6),
            verdict=last_verdict,
            verification_passed=verification_passed,
        )
