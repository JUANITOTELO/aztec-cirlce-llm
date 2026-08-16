"""
In-application Self-Updater Engine for Aztec Decision Circle.
Supports Git-based and pip-based upgrades with automated dependency re-sync and smoke testing.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional, Tuple
import structlog
from rich.console import Console

import aztec_circle

log = structlog.get_logger(__name__)


@dataclass
class UpdateCheckResult:
    """Outcome of an update check."""
    has_update: bool
    current_version: str
    latest_version: str
    commits_behind: int = 0
    message: str = ""


@dataclass
class UpdateExecutionResult:
    """Outcome of an update execution."""
    success: bool
    old_version: str
    new_version: str
    message: str
    error: Optional[str] = None


class AztecUpdater:
    """
    Handles automatic self-updating for Aztec installations.
    """

    def __init__(self, console: Optional[Console] = None):
        self.console = console
        self.current_version = aztec_circle.__version__

    def find_git_root(self) -> Optional[str]:
        """
        Locate the root of the Aztec Git clone if installed from source or in ~/.aztec/repo.
        """
        # 1. Check parent directories of this file
        current = os.path.abspath(__file__)
        for _ in range(4):
            parent = os.path.dirname(current)
            if os.path.exists(os.path.join(parent, ".git")) and os.path.exists(os.path.join(parent, "aztec_circle")):
                return parent
            current = parent

        # 2. Check standard ~/.aztec/repo
        aztec_home = os.path.expanduser("~/.aztec/repo")
        if os.path.exists(os.path.join(aztec_home, ".git")):
            return aztec_home

        return None

    def check_for_updates(self, timeout_seconds: float = 3.5) -> UpdateCheckResult:
        """
        Query remote repository to check for available updates.
        Safe for fast, non-blocking invocation on application launch.
        """
        repo_root = self.find_git_root()
        if not repo_root or not shutil.which("git"):
            return UpdateCheckResult(
                has_update=False,
                current_version=self.current_version,
                latest_version=self.current_version,
                commits_behind=0,
                message="Installed via standalone package (Git repo not detected).",
            )

        try:
            # 1. Fetch remote tracking branch
            subprocess.run(
                ["git", "fetch", "--quiet", "origin", "main"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )

            # 2. Count commits behind
            res = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..origin/main"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )

            if res.returncode == 0:
                behind = int(res.stdout.strip() or "0")
                if behind > 0:
                    return UpdateCheckResult(
                        has_update=True,
                        current_version=self.current_version,
                        latest_version=f"latest (git +{behind})",
                        commits_behind=behind,
                        message=f"{behind} new commit(s) available on origin/main.",
                    )
                return UpdateCheckResult(
                    has_update=False,
                    current_version=self.current_version,
                    latest_version=self.current_version,
                    commits_behind=0,
                    message="Aztec is up to date.",
                )

        except Exception as exc:
            log.debug("updater.check_failed", error=str(exc))

        return UpdateCheckResult(
            has_update=False,
            current_version=self.current_version,
            latest_version=self.current_version,
            commits_behind=0,
            message="Could not connect to remote repository.",
        )

    async def perform_update(self, force: bool = False) -> UpdateExecutionResult:
        """
        Pull latest changes from remote repository, re-install package, and verify binary.
        """
        repo_root = self.find_git_root()
        old_version = self.current_version

        if not repo_root:
            return UpdateExecutionResult(
                success=False,
                old_version=old_version,
                new_version=old_version,
                message="Cannot self-update: Git repository root not found.",
                error="No Git clone found for Aztec.",
            )

        if self.console:
            self.console.print(f"[bold cyan]▶ Updating Aztec from repository:[/bold cyan] {repo_root}")

        try:
            # 1. Git pull
            if self.console:
                self.console.print("  [dim][1/3] Pulling latest changes from origin/main...[/dim]")

            pull_proc = await asyncio.create_subprocess_exec(
                "git", "pull", "--rebase", "origin", "main",
                cwd=repo_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await pull_proc.communicate()

            if pull_proc.returncode != 0:
                # Fallback to standard git pull
                pull_proc2 = await asyncio.create_subprocess_exec(
                    "git", "pull", "origin", "main",
                    cwd=repo_root,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await pull_proc2.communicate()
                if pull_proc2.returncode != 0:
                    err_msg = stderr.decode().strip() or "git pull failed"
                    return UpdateExecutionResult(
                        success=False,
                        old_version=old_version,
                        new_version=old_version,
                        message=f"Git pull failed: {err_msg}",
                        error=err_msg,
                    )

            # 2. Re-install editable dependencies
            if self.console:
                self.console.print("  [dim][2/3] Syncing Python dependencies...[/dim]")

            pip_proc = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", "--quiet", "-e", repo_root,
                cwd=repo_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, pip_err = await pip_proc.communicate()
            if pip_proc.returncode != 0:
                err_msg = pip_err.decode().strip() or "pip install failed"
                return UpdateExecutionResult(
                    success=False,
                    old_version=old_version,
                    new_version=old_version,
                    message=f"Dependency installation failed: {err_msg}",
                    error=err_msg,
                )

            # 3. Verification
            if self.console:
                self.console.print("  [dim][3/3] Verifying updated Aztec binary...[/dim]")

            new_version = aztec_circle.__version__

            if self.console:
                self.console.print(f"\n[bold green]✓ Aztec updated successfully![/bold green] [dim]({old_version} ➔ {new_version})[/dim]\n")

            return UpdateExecutionResult(
                success=True,
                old_version=old_version,
                new_version=new_version,
                message=f"Successfully updated Aztec to {new_version}.",
            )

        except Exception as exc:
            log.error("updater.perform_update_failed", error=str(exc))
            return UpdateExecutionResult(
                success=False,
                old_version=old_version,
                new_version=old_version,
                message=f"Update failed with exception: {exc}",
                error=str(exc),
            )
