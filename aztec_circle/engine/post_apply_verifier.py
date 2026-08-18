"""
PostApplyVerifier — Verifies compilation / types across the project post-apply.
Detects ecosystem, executes compiler/type-checkers, and surfaces diagnostics to BuildFixer.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import structlog
from rich.console import Console

from aztec_circle.engine.project_runner import CommandResult, ProjectRunner
from aztec_circle.engine.scaffolder import find_project_root, detect_project_ecosystem

log = structlog.get_logger(__name__)


@dataclass
class VerificationResult:
    """Outcome of a post-apply type and compilation verification run."""
    success: bool
    command_used: str
    stdout: str = ""
    stderr: str = ""
    error_count: int = 0
    errors_summary: str = ""
    command_result: Optional[CommandResult] = None


ECOSYSTEM_VERIFIERS: Dict[str, str] = {
    "vite-react": "npx tsc --noEmit 2>&1",
    "vite-react-ts": "npx tsc --noEmit 2>&1",
    "next": "npx tsc --noEmit 2>&1",
    "generic-ts": "npx tsc --noEmit 2>&1",
    "php": "php -l backend/index.php 2>&1",
}


class PostApplyVerifier:
    """
    Executes post-apply verification checks to detect compile-time
    type mismatches, missing imports, or syntax defects.
    """

    def __init__(
        self,
        project_root: str,
        console: Optional[Console] = None,
        runner: Optional[ProjectRunner] = None,
    ):
        self.root = find_project_root(project_root) or project_root
        self.console = console
        self.runner = runner or ProjectRunner(console=console)

    async def verify(
        self,
        ecosystem: Optional[str] = None,
        custom_command: Optional[str] = None,
    ) -> VerificationResult:
        """
        Run type-checking or compile verification for the project ecosystem.
        """
        eco = ecosystem or detect_project_ecosystem(self.root)
        cmd = custom_command or ECOSYSTEM_VERIFIERS.get(eco)

        # Fallback: check if tsconfig.json exists
        if not cmd and os.path.exists(os.path.join(self.root, "tsconfig.json")):
            cmd = "npx tsc --noEmit 2>&1"

        if not cmd:
            log.info("post_apply_verifier.skipped", ecosystem=eco, reason="no verifier registered")
            return VerificationResult(
                success=True,
                command_used="(no verifier registered)",
                stdout="Verification skipped: no verifier command configured.",
            )

        log.info("post_apply_verifier.started", command=cmd, ecosystem=eco, root=self.root)
        if self.console:
            self.console.print(f"  [cyan]🔍 Running post-apply type verification:[/cyan] [dim]{cmd}[/dim]")

        result: CommandResult = await self.runner.run_shell_command_streamed(
            cmd_str=cmd,
            cwd=self.root,
            title="Post-Apply Type Verification",
        )

        combined_output = f"{result.stdout}\n{result.stderr}".strip()
        error_lines = [
            line.strip()
            for line in combined_output.splitlines()
            if "error " in line.lower() or ": error" in line.lower() or "fail" in line.lower()
        ]

        is_success = result.success and (len(error_lines) == 0)

        summary = "\n".join(error_lines[:25]) if error_lines else (combined_output[:500] if not is_success else "")

        return VerificationResult(
            success=is_success,
            command_used=cmd,
            stdout=result.stdout,
            stderr=result.stderr,
            error_count=len(error_lines),
            errors_summary=summary,
            command_result=result,
        )

    async def verify_tests(self, custom_test_command: Optional[str] = None) -> VerificationResult:
        """
        Executes automated test suite to ensure no behavioral regressions.
        """
        cmd = custom_test_command
        if not cmd:
            pkg_json = os.path.join(self.root, "package.json")
            if os.path.exists(pkg_json):
                cmd = "npm test -- --run 2>&1"
            elif os.path.exists(os.path.join(self.root, "pytest.ini")) or os.path.exists(os.path.join(self.root, "tests")):
                cmd = "pytest 2>&1"

        if not cmd:
            return VerificationResult(
                success=True,
                command_used="(no test runner detected)",
                stdout="No test runner detected.",
            )

        log.info("post_apply_verifier.running_tests", command=cmd, root=self.root)
        if self.console:
            self.console.print(f"  [cyan]🧪 Running post-apply test suite:[/cyan] [dim]{cmd}[/dim]")

        result: CommandResult = await self.runner.run_shell_command_streamed(
            cmd_str=cmd,
            cwd=self.root,
            title="Post-Apply Test Verification",
        )

        combined = f"{result.stdout}\n{result.stderr}".strip()
        failed_lines = [
            l.strip()
            for l in combined.splitlines()
            if "fail" in l.lower() or "error" in l.lower() or "failed" in l.lower()
        ]
        is_success = result.success and (result.exit_code == 0)
        summary = "\n".join(failed_lines[:25]) if failed_lines else (combined[:500] if not is_success else "")

        return VerificationResult(
            success=is_success,
            command_used=cmd,
            stdout=result.stdout,
            stderr=result.stderr,
            error_count=len(failed_lines) if not is_success else 0,
            errors_summary=summary,
            command_result=result,
        )

    async def verify_all(
        self,
        ecosystem: Optional[str] = None,
        run_tests: bool = False,
    ) -> VerificationResult:
        """
        Runs type-checking and optional test verification in sequence.
        """
        tc_res = await self.verify(ecosystem=ecosystem)
        if not tc_res.success:
            return tc_res

        if run_tests:
            test_res = await self.verify_tests()
            if not test_res.success:
                return test_res

        return tc_res
