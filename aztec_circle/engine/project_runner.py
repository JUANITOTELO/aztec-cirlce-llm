"""
Project Runner & Build Engine for Aztec Decision Circle.
Executes dependencies installation, builds, test runners, and live dev server daemons.
"""

from __future__ import annotations

import asyncio
import os
import re
import socket
import time
from dataclasses import dataclass
from typing import Callable, Optional
from rich.console import Console

from aztec_circle.engine.scaffolder import find_project_root, detect_project_ecosystem


class PortInUseError(Exception):
    """Raised when a dev server port is already bound."""
    pass


@dataclass
class CommandResult:
    """Represents the execution result of a build or test command."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_seconds: float


@dataclass
class ServerProcess:
    """Manages an active background development server."""
    process: asyncio.subprocess.Process
    port: int
    url: str
    project_dir: str

    async def stop(self) -> None:
        """Gracefully terminate dev server process."""
        if self.process.returncode is None:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=3.0)
            except Exception:
                try:
                    self.process.kill()
                    await self.process.wait()
                except Exception:
                    pass


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is open for binding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        res = s.connect_ex((host, port))
        return res != 0


class ProjectRunner:
    """Executes build, test, and dev server lifecycle tasks on generated projects."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console

    async def run_command_streamed(
        self,
        cmd: list[str],
        cwd: str,
        title: str = "Command",
    ) -> CommandResult:
        """Run an async subprocess while streaming its output in real time."""
        if self.console:
            self.console.print(f"[bold cyan]▶ {title}:[/bold cyan] [dim]{' '.join(cmd)}[/dim]")

        start_time = time.monotonic()
        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async def _read_stdout():
                assert proc.stdout is not None
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace")
                    stdout_lines.append(decoded)
                    if self.console:
                        self.console.print(f"  [dim]{decoded.rstrip()}[/dim]")

            async def _read_stderr():
                assert proc.stderr is not None
                while True:
                    line = await proc.stderr.readline()
                    if not line:
                        break
                    decoded = line.decode("utf-8", errors="replace")
                    stderr_lines.append(decoded)
                    if self.console:
                        self.console.print(f"  [red]{decoded.rstrip()}[/red]")

            await asyncio.gather(_read_stdout(), _read_stderr())
            await proc.wait()

            duration = time.monotonic() - start_time
            exit_code = proc.returncode or 0
            success = exit_code == 0

            full_stdout = "".join(stdout_lines)
            full_stderr = "".join(stderr_lines)

            if self.console:
                if success:
                    self.console.print(f"  [bold green]✓ {title} passed[/bold green] [dim]({duration:.2f}s)[/dim]\n")
                else:
                    self.console.print(f"  [bold red]✗ {title} failed[/bold red] [dim](exit code {exit_code})[/dim]\n")

            return CommandResult(
                success=success,
                stdout=full_stdout,
                stderr=full_stderr,
                exit_code=exit_code,
                duration_seconds=duration,
            )

        except Exception as exc:
            duration = time.monotonic() - start_time
            if self.console:
                self.console.print(f"  [bold red]✗ {title} error:[/bold red] {exc}\n")
            return CommandResult(
                success=False,
                stdout="".join(stdout_lines),
                stderr=str(exc),
                exit_code=-1,
                duration_seconds=duration,
            )

    async def install_dependencies(self, project_dir: str) -> CommandResult:
        """Install dependencies based on detected project ecosystem."""
        root = find_project_root(project_dir)
        ecosystem = detect_project_ecosystem(root)

        if ecosystem in ("vite_react", "node"):
            return await self.run_command_streamed(
                cmd=["npm", "install"],
                cwd=root,
                title="Installing Node Dependencies (npm install)",
            )
        elif ecosystem == "python":
            pyproj = os.path.join(root, "pyproject.toml")
            reqs = os.path.join(root, "requirements.txt")
            if os.path.exists(pyproj):
                cmd = ["pip", "install", "-e", "."]
            elif os.path.exists(reqs):
                cmd = ["pip", "install", "-r", "requirements.txt"]
            else:
                cmd = ["pip", "install", "-e", "."]

            return await self.run_command_streamed(
                cmd=cmd,
                cwd=root,
                title="Installing Python Dependencies",
            )
        else:
            return CommandResult(success=True, stdout="Generic project, no installer needed", stderr="", exit_code=0, duration_seconds=0.0)

    async def build_project(self, project_dir: str) -> CommandResult:
        """Build and typecheck the project."""
        root = find_project_root(project_dir)
        ecosystem = detect_project_ecosystem(root)

        if ecosystem in ("vite_react", "node"):
            return await self.run_command_streamed(
                cmd=["npm", "run", "build"],
                cwd=root,
                title="Building Project (npm run build)",
            )
        elif ecosystem == "python":
            return await self.run_command_streamed(
                cmd=["python3", "-m", "compileall", "."],
                cwd=root,
                title="Compiling Python Bytecode",
            )
    async def typecheck_project(self, project_dir: str) -> CommandResult:
        """Execute non-destructive TypeScript compiler check without emitting files."""
        root = find_project_root(project_dir)
        ecosystem = detect_project_ecosystem(root)

        if ecosystem in ("vite_react", "node"):
            return await self.run_command_streamed(
                cmd=["npx", "tsc", "--noEmit"],
                cwd=root,
                title="TypeScript Type Check (tsc --noEmit)",
            )
        elif ecosystem == "python":
            return await self.run_command_streamed(
                cmd=["python3", "-m", "py_compile"],
                cwd=root,
                title="Python Syntax Validation",
            )
        else:
            return CommandResult(success=True, stdout="No type check step defined", stderr="", exit_code=0, duration_seconds=0.0)

    async def test_project(self, project_dir: str) -> CommandResult:
        """Execute project test suite."""
        root = find_project_root(project_dir)
        ecosystem = detect_project_ecosystem(root)

        if ecosystem in ("vite_react", "node"):
            return await self.run_command_streamed(
                cmd=["npm", "test"],
                cwd=root,
                title="Running Test Suite (npm test)",
            )
        elif ecosystem == "python":
            return await self.run_command_streamed(
                cmd=["pytest"],
                cwd=root,
                title="Running Python Test Suite (pytest)",
            )
        else:
            return CommandResult(success=True, stdout="No test suite defined", stderr="", exit_code=0, duration_seconds=0.0)

    async def start_dev_server(
        self,
        project_dir: str,
        port: int = 5173,
        on_ready: Optional[Callable[[str], None]] = None,
    ) -> ServerProcess:
        """
        Start development server daemon in background and wait for live URL.
        """
        root = find_project_root(project_dir)
        ecosystem = detect_project_ecosystem(root)

        if not is_port_available(port):
            raise PortInUseError(f"Port {port} is already in use. Specify a different port with --port.")

        if ecosystem in ("vite_react", "node"):
            cmd = ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", str(port)]
        elif ecosystem == "python":
            cmd = ["python3", "-m", "http.server", str(port)]
        else:
            cmd = ["python3", "-m", "http.server", str(port)]

        if self.console:
            self.console.print(f"[bold cyan]▶ Spawning Dev Server:[/bold cyan] [dim]{' '.join(cmd)}[/dim]")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        detected_url = f"http://localhost:{port}"
        ready_event = asyncio.Event()

        async def _monitor_stream():
            assert proc.stdout is not None
            url_regex = re.compile(r"(http://localhost:\d+|http://127\.0\.0\.1:\d+|http://0\.0\.0\.0:\d+)")
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace")
                if self.console:
                    self.console.print(f"  [dim]{decoded.rstrip()}[/dim]")
                match = url_regex.search(decoded)
                if match:
                    nonlocal detected_url
                    detected_url = match.group(1).replace("0.0.0.0", "localhost")
                    ready_event.set()
                    if on_ready:
                        on_ready(detected_url)

        asyncio.create_task(_monitor_stream())

        # Wait up to 5 seconds for Vite/Server startup banner, otherwise default to configured URL
        try:
            await asyncio.wait_for(ready_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            pass

        if self.console:
            self.console.print(f"\n[bold green]🚀 Live Application Server Running at:[/bold green] [bold underline cyan]{detected_url}[/bold underline cyan]\n")

        return ServerProcess(process=proc, port=port, url=detected_url, project_dir=root)
