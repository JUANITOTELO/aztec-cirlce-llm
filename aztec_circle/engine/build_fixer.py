"""
Build Error Auto-Fixer for Aztec Decision Circle.
Parses compiler and build errors (TypeScript / Vite / Python) and uses targeted, atomic
LLM calls to repair failing source files one file at a time.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import structlog
from rich.console import Console

from aztec_circle.adapters.llm_provider import LLMProvider, LLMResponse
from aztec_circle.agents.base import extract_json_payload
from aztec_circle.config import settings
from aztec_circle.engine.budget_manager import BudgetManager
from aztec_circle.engine.project_runner import CommandResult, ProjectRunner
from aztec_circle.engine.scaffolder import find_project_root

log = structlog.get_logger(__name__)

TS_ERROR_PATTERN = re.compile(
    r"^(?P<file>[^\s(]+)\((?P<line>\d+),\d+\): error (?P<code>TS\d+): (?P<msg>.+)$",
    re.MULTILINE,
)

PHP_ERROR_PATTERN = re.compile(
    r"(?:PHP Fatal error|Fatal error|Parse error|PHP Parse error):\s+(?P<msg>.+?)\s+in\s+(?P<file>.+?)\s+on\s+line\s+(?P<line>\d+)",
    re.IGNORECASE | re.MULTILINE,
)

PYTHON_ERROR_PATTERN = re.compile(
    r'File "(?P<file>[^"]+)", line (?P<line>\d+).*?\n\s*(?P<msg>[A-Za-z0-9_]+Error:\s*.+)',
    re.DOTALL,
)

LEAN_ERROR_PATTERN = re.compile(
    r"^(?P<file>[^\s:]+\.lean):(?P<line>\d+):(?P<col>\d+):\s+error:\s+(?P<msg>.+)$",
    re.MULTILINE,
)


@dataclass
class TSError:
    """Represents an individual compiler or test error diagnostic."""
    file: str
    line: int
    code: str
    message: str


@dataclass
class FixResult:
    """Summary of a build auto-repair operation."""
    success: bool
    iterations: int
    final_build_result: CommandResult
    patches_applied: List[str] = field(default_factory=list)
    total_cost_usd: float = 0.0


class BuildFixAgent:
    """
    Automated self-healing multi-tier build and test error repair agent.
    Extracts compiler diagnostics (TypeScript, PHP, Python, SQL, Lean 4), groups them by file,
    and prompts LLM for targeted atomic file repairs.
    """

    SYSTEM_PROMPT = """You are an expert Multi-Tier Software Engineer & Build Repair Specialist (TypeScript, React, PHP, Python, SQL, Lean 4).
Your task is to fix build, test, and compilation errors in the provided project files.

You will receive:
1. The exact compiler / test / runtime errors for a file.
2. The full content of that file.

CRITICAL INSTRUCTIONS:
- You must output ONLY a valid JSON object strictly matching this schema:
  {
    "fixes_summary": "string: brief explanation of fixes applied",
    "patched_files": {
      "relative/path/to/file.ext": "string: complete, full corrected source code for the file"
    }
  }
- Provide the COMPLETE corrected file content for the file. Never use placeholders or truncation comments like "// ... rest of code".
- Fix all errors shown (missing imports, unhandled SQL dialects, type mismatches, missing test setups, syntax errors).
- Keep files modular and clean.
- Respond ONLY with the JSON object.
"""

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        console: Optional[Console] = None,
        max_iterations: int = 2,
        model: Optional[str] = None,
    ):
        self.provider = provider or LLMProvider()
        self.console = console
        self.max_iterations = max_iterations
        self.model = model or settings.get_effective_model("FIXER")

    def parse_errors(self, build_output: str) -> List[TSError]:
        """Extract structured errors from compiler diagnostics across TS, PHP, Python, and Lean."""
        errors: List[TSError] = []
        
        # 1. TypeScript errors
        for match in TS_ERROR_PATTERN.finditer(build_output):
            errors.append(
                TSError(
                    file=match.group("file").strip(),
                    line=int(match.group("line")),
                    code=match.group("code").strip(),
                    message=match.group("msg").strip(),
                )
            )

        # 2. PHP errors
        for match in PHP_ERROR_PATTERN.finditer(build_output):
            errors.append(
                TSError(
                    file=match.group("file").strip(),
                    line=int(match.group("line")),
                    code="PHP_ERROR",
                    message=match.group("msg").strip(),
                )
            )

        # 3. Lean 4 errors
        for match in LEAN_ERROR_PATTERN.finditer(build_output):
            errors.append(
                TSError(
                    file=match.group("file").strip(),
                    line=int(match.group("line")),
                    code="LEAN_ERROR",
                    message=match.group("msg").strip(),
                )
            )

        return errors

    async def fix(
        self,
        project_dir: str,
        initial_build_result: CommandResult,
        runner: Optional[ProjectRunner] = None,
    ) -> FixResult:
        """
        Execute iterative self-healing fix loop until build succeeds or max_iterations reached.
        Operates atomically on one failing file at a time per iteration.
        """
        runner = runner or ProjectRunner(console=self.console)
        root = find_project_root(project_dir)
        current_build = initial_build_result
        all_patched: List[str] = []
        total_cost = 0.0

        if current_build.success:
            return FixResult(
                success=True,
                iterations=0,
                final_build_result=current_build,
                patches_applied=[],
                total_cost_usd=0.0,
            )

        if self.console:
            self.console.print(f"\n[bold yellow]🔧 Initiating Aztec Build Self-Healing Engine (Max {self.max_iterations} iterations)[/bold yellow]")

        for loop in range(1, self.max_iterations + 1):
            combined_log = f"{current_build.stderr}\n{current_build.stdout}"
            errors = self.parse_errors(combined_log)

            if not errors and not combined_log.strip():
                break

            # Group errors by file
            errors_by_file: Dict[str, List[TSError]] = {}
            for e in errors:
                errors_by_file.setdefault(e.file, []).append(e)

            target_files = list(errors_by_file.keys())
            if not target_files:
                for f in ["src/App.tsx", "src/main.tsx", "src/utils/constants.ts"]:
                    if os.path.exists(os.path.join(root, f)):
                        target_files.append(f)
                        errors_by_file[f] = []

            if not target_files:
                if self.console:
                    self.console.print("  [red]Could not locate affected source files on disk to repair.[/red]")
                break

            if self.console:
                self.console.print(f"  [cyan]Iteration {loop}/{self.max_iterations}:[/cyan] Found {len(errors) if errors else 'build'} error(s) across {len(target_files)} file(s). Repairing atomically...")

            # Repair each file in this iteration
            iteration_patched = 0
            for rel_path in target_files:
                clean_path = rel_path.lstrip("/\\").replace("\\", "/")
                full_path = os.path.join(root, clean_path)

                if not os.path.exists(full_path):
                    continue

                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                        file_content = fh.read()
                except Exception as err:
                    log.warning("build_fixer.read_file_error", path=full_path, error=str(err))
                    continue

                file_errors = errors_by_file.get(rel_path, [])
                error_summary = "\n".join(
                    f"- {e.file}:{e.line} [{e.code}] {e.message}" for e in file_errors
                ) if file_errors else combined_log[:1500]

                user_prompt = f"""BUILD ERRORS DETECTED IN {clean_path}:
{error_summary}

CURRENT FILE CONTENT:
```
{file_content}
```

Please output the complete, corrected code for {clean_path}."""

                from aztec_circle.tui.streaming_ui import SingleStreamVisualizer
                fix_vis = SingleStreamVisualizer(
                    console=self.console,
                    title=f"Repairing {clean_path} (Iteration {loop})",
                    icon="🔧",
                    show_preview=True,
                )
                try:
                    with fix_vis:
                        resp: LLMResponse = await self.provider.invoke(
                            model=self.model,
                            system_prompt=self.SYSTEM_PROMPT,
                            user_message=user_prompt,
                            temperature=0.1,
                            on_chunk=fix_vis.on_chunk,
                        )
                    bm = BudgetManager()
                    cost = bm.record(
                        input_tokens=resp.prompt_tokens,
                        output_tokens=resp.completion_tokens,
                        total_tokens=resp.total_tokens,
                        cached_tokens=resp.cached_tokens,
                    )
                    total_cost += cost

                    data = extract_json_payload(resp.content)
                    patched_files: Dict[str, str] = data.get("patched_files", {})

                    if not patched_files:
                        for k, v in data.items():
                            if isinstance(v, str) and (k.endswith((".ts", ".tsx", ".js", ".jsx", ".json", ".css")) or "/" in k):
                                patched_files[k] = v

                    if not patched_files and "fixes_summary" in data:
                        # Check if entire content was returned in a content key
                        if "content" in data and isinstance(data["content"], str):
                            patched_files[clean_path] = data["content"]

                    for p_rel, new_content in patched_files.items():
                        c_path = p_rel.lstrip("/\\").replace("\\", "/")
                        target_write_path = os.path.join(root, c_path)
                        os.makedirs(os.path.dirname(target_write_path), exist_ok=True)
                        with open(target_write_path, "w", encoding="utf-8") as fh:
                            fh.write(new_content)
                        if c_path not in all_patched:
                            all_patched.append(c_path)
                        iteration_patched += 1
                        if self.console:
                            self.console.print(f"    [green]✓[/green] Atomically repaired: [bold]{c_path}[/bold]")

                except Exception as exc:
                    log.error("build_fixer.atomic_file_fix_error", file=clean_path, error=str(exc))
                    if self.console:
                        self.console.print(f"    [red]Failed to repair {clean_path}:[/red] {exc}")

            if iteration_patched == 0:
                if self.console:
                    self.console.print("  [yellow]No files were patched in this iteration.[/yellow]")
                break

            if self.console:
                self.console.print("  [cyan]Re-running build verification...[/cyan]")

            # Re-run build to verify
            current_build = await runner.build_project(root)
            if current_build.success:
                if self.console:
                    self.console.print(f"  [bold green]🎉 Build healed successfully in iteration {loop}![/bold green]\n")
                from aztec_circle.engine.plan_manager import PlanManager
                PlanManager.record_fix_iteration(output_dir=root, fixed_files=all_patched)
                return FixResult(
                    success=True,
                    iterations=loop,
                    final_build_result=current_build,
                    patches_applied=all_patched,
                    total_cost_usd=round(total_cost, 6),
                )

        if all_patched:
            from aztec_circle.engine.plan_manager import PlanManager
            PlanManager.record_fix_iteration(output_dir=root, fixed_files=all_patched)

        return FixResult(
            success=current_build.success,
            iterations=self.max_iterations,
            final_build_result=current_build,
            patches_applied=all_patched,
            total_cost_usd=round(total_cost, 6),
        )
