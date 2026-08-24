"""
In-application Self-Updater Engine for Aztec Decision Circle.
Supports Git-based upgrades with automated dependency re-sync and verification.

Safety rules (learned the hard way):
- Never silently rebases or discards local commits: divergence requires
  explicit --force and even then uses an explicit rebase pull.
- Refuses to operate on a dirty worktree.
- Honors the actual checked-out branch instead of hardcoding main.
"""

from __future__ import annotations

import asyncio
import importlib.metadata
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

_PACKAGE_NAME_CANDIDATES = ("aztec-circle", "aztec_circle")


@dataclass
class UpdateCheckResult:
    """Outcome of an update check."""
    has_update: bool
    current_version: str
    latest_version: str
    commits_behind: int = 0
    local_commits: int = 0
    branch: str = "main"
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

    # ── Low-level git helpers (seams for tests) ──────────────────────────
    def _run_sync(self, repo_root: str, *args: str, timeout: float = 6.0) -> Tuple[int, str, str]:
        try:
            res = subprocess.run(
                ["git", *args],
                cwd=repo_root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return res.returncode, (res.stdout or "").strip(), (res.stderr or "").strip()
        except Exception as exc:
            return -1, "", str(exc)

    def find_git_root(self) -> Optional[str]:
        """
        Locate the root of the Aztec Git clone if installed from source or in ~/.aztec/repo.
        """
        # 1. Check parent directories of this file
        current = os.path.abspath(__file__)
        for _ in range(6):
            parent = os.path.dirname(current)
            if os.path.exists(os.path.join(parent, ".git")) and os.path.exists(os.path.join(parent, "aztec_circle")):
                return parent
            current = parent

        # 2. Check standard ~/.aztec/repo
        aztec_home = os.path.expanduser("~/.aztec/repo")
        if os.path.exists(os.path.join(aztec_home, ".git")):
            return aztec_home

        return None

    def current_branch(self, repo_root: str) -> str:
        rc, out, _ = self._run_sync(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
        if rc == 0 and out and out != "HEAD":
            return out
        return "main"

    def has_dirty_worktree(self, repo_root: str) -> bool:
        # -uno: untracked artifacts (databases, logs, caches) cannot conflict
        # with a pull and must not block updates; only tracked-file
        # modifications count as dirty.
        rc, out, _ = self._run_sync(repo_root, "status", "--porcelain", "-uno")
        return rc == 0 and bool(out)

    def _count_commits(self, repo_root: str, range_expr: str) -> int:
        rc, out, _ = self._run_sync(repo_root, "rev-list", "--count", range_expr)
        if rc != 0:
            return -1
        try:
            return int(out or "0")
        except ValueError:
            return -1

    # ── Public API ────────────────────────────────────────────────────────
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
                message="Installed via standalone package (Git repo not detected).",
            )

        branch = self.current_branch(repo_root)
        try:
            rc, _, _ = self._run_sync(
                repo_root, "fetch", "--quiet", "origin", branch,
                timeout=timeout_seconds,
            )
            behind = self._count_commits(repo_root, f"HEAD..origin/{branch}")
            local = self._count_commits(repo_root, f"origin/{branch}..HEAD")

            if behind >= 0:
                if behind > 0:
                    return UpdateCheckResult(
                        has_update=True,
                        current_version=self.current_version,
                        latest_version=f"latest (git +{behind})",
                        commits_behind=behind,
                        local_commits=max(0, local),
                        branch=branch,
                        message=f"{behind} new commit(s) available on origin/{branch}.",
                    )
                return UpdateCheckResult(
                    has_update=False,
                    current_version=self.current_version,
                    latest_version=self.current_version,
                    commits_behind=0,
                    local_commits=max(0, local),
                    branch=branch,
                    message="Aztec is up to date.",
                )
        except Exception as exc:
            log.debug("updater.check_failed", error=str(exc))

        return UpdateCheckResult(
            has_update=False,
            current_version=self.current_version,
            latest_version=self.current_version,
            branch=branch,
            message="Could not connect to remote repository.",
        )

    def _fresh_installed_version(self) -> str:
        """
        Read the on-disk package version after reinstall. The module-level
        aztec_circle.__version__ is frozen at first import, so consult package
        metadata first and fall back to it.
        """
        for name in _PACKAGE_NAME_CANDIDATES:
            try:
                return importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                continue
        return aztec_circle.__version__

    def _say(self, markup: str) -> None:
        if self.console:
            self.console.print(markup)

    async def perform_update(self, force: bool = False) -> UpdateExecutionResult:
        """
        Pull latest changes from the remote repository, re-install the package,
        and report the refreshed version.

        Safety semantics:
        - Dirty worktree           -> refuse (commit or stash first).
        - Nothing to pull          -> clean early-exit, zero git mutations.
        - Local commits + upstream -> refuse unless force=True (then explicit
          `git pull --rebase`; never a silent history rewrite).
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

        self._say(f"[bold cyan]▶ Updating Aztec from repository:[/bold cyan] {repo_root}")

        # ── Preflight guards ──────────────────────────────────────────────
        if self.has_dirty_worktree(repo_root):
            msg = (
                "Worktree has uncommitted changes. "
                "Commit or stash them before updating."
            )
            self._say(f"[bold red]✗ Update aborted:[/bold red] {msg}")
            return UpdateExecutionResult(
                success=False,
                old_version=old_version,
                new_version=old_version,
                message=msg,
                error="dirty-worktree",
            )

        branch = self.current_branch(repo_root)
        preflight = self.check_for_updates()

        if not preflight.has_update:
            note = ""
            if preflight.local_commits > 0:
                note = f" [dim]({preflight.local_commits} local commit(s) not yet pushed)[/dim]"
            msg = f"Aztec is already up to date.{note}"
            self._say(f"[green]✓ {msg}[/green] [dim](v{old_version})[/dim]")
            return UpdateExecutionResult(
                success=True,
                old_version=old_version,
                new_version=old_version,
                message=msg,
            )

        if preflight.local_commits > 0 and not force:
            msg = (
                f"{preflight.local_commits} local commit(s) diverge from origin/{branch}; "
                "a fast-forward is impossible. Push/stash your work, or rerun with "
                "`--force` to rebase local commits on top."
            )
            self._say(f"[bold yellow]⚠ Update blocked:[/bold yellow] {msg}")
            return UpdateExecutionResult(
                success=False,
                old_version=old_version,
                new_version=old_version,
                message=msg,
                error="diverged-history",
            )

        # ── Step 1: Pull ──────────────────────────────────────────────────
        self._say(f"  [dim][1/3] Pulling latest changes from origin/{branch}...[/dim]")
        pull_mode = "--rebase" if (force and preflight.local_commits > 0) else "--ff-only"
        pull_rc, pull_out, pull_err = await self._run_async_git(
            repo_root, "pull", pull_mode, "origin", branch
        )
        if pull_rc != 0:
            err_msg = pull_err or pull_out or f"git pull {pull_mode} failed"
            self._say(f"[bold red]✗ Git pull failed:[/bold red] {err_msg}")
            return UpdateExecutionResult(
                success=False,
                old_version=old_version,
                new_version=old_version,
                message=f"Git pull failed: {err_msg}",
                error=err_msg,
            )

        # ── Step 2: Re-sync dependencies ──────────────────────────────────
        self._say("  [dim][2/3] Syncing Python dependencies...[/dim]")
        pip_rc, _, pip_err = await self._run_async_pip(repo_root)
        if pip_rc != 0:
            err_msg = pip_err.strip() or "pip install failed"
            self._say(f"[bold red]✗ Dependency installation failed:[/bold red] {err_msg}")
            return UpdateExecutionResult(
                success=False,
                old_version=old_version,
                new_version=old_version,
                message=f"Dependency installation failed: {err_msg}",
                error=err_msg,
            )

        # ── Step 3: Verification ──────────────────────────────────────────
        self._say("  [dim][3/3] Verifying updated installation...[/dim]")
        new_version = self._fresh_installed_version()

        self._say(
            f"\n[bold green]✓ Aztec updated successfully![/bold green] "
            f"[dim]({old_version} ➔ {new_version}, {preflight.commits_behind} commit(s) pulled)[/dim]\n"
        )
        return UpdateExecutionResult(
            success=True,
            old_version=old_version,
            new_version=new_version,
            message=f"Successfully updated Aztec to {new_version}.",
        )

    # ── Async subprocess helpers ──────────────────────────────────────────
    async def _run_async_git(self, repo_root: str, *args: str) -> Tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=repo_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return (proc.returncode or 0), stdout.decode(errors="replace").strip(), stderr.decode(errors="replace").strip()

    async def _run_async_pip(self, repo_root: str) -> Tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "pip", "install", "--quiet", "-e", repo_root,
            cwd=repo_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        return (proc.returncode or 0), "", stderr.decode(errors="replace")
