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
    log_file: Optional[str] = None
    monitor_task: Optional[asyncio.Task] = None

    async def stop(self) -> None:
        """Gracefully terminate dev server process and its process group."""
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
        if self.process.returncode is None:
            try:
                import signal
                try:
                    pgid = os.getpgid(self.process.pid)
                    os.killpg(pgid, signal.SIGTERM)
                except Exception:
                    self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=3.0)
            except Exception:
                try:
                    import signal
                    try:
                        pgid = os.getpgid(self.process.pid)
                        os.killpg(pgid, signal.SIGKILL)
                    except Exception:
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
        """Execute command asynchronously with streaming Rich output."""
        if self.console:
            self.console.print(f"[bold cyan]▶ {title}:[/bold cyan] [dim]{' '.join(cmd)}[/dim]")

        start_time = time.time()
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout_chunks: list[str] = []
        stderr_chunks: list[str] = []

        async def _read_stream(stream, is_err=False):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace")
                if is_err:
                    stderr_chunks.append(decoded)
                    if self.console:
                        self.console.print(f"  [red]{decoded.rstrip()}[/red]")
                else:
                    stdout_chunks.append(decoded)
                    if self.console:
                        self.console.print(f"  [dim]{decoded.rstrip()}[/dim]")

        await asyncio.gather(
            _read_stream(proc.stdout, is_err=False),
            _read_stream(proc.stderr, is_err=True),
        )

        returncode = await proc.wait()
        duration = time.time() - start_time
        success = (returncode == 0)

        if self.console:
            if success:
                self.console.print(f"  [bold green]✓ {title} passed ({duration:.2f}s)[/bold green]\n")
            else:
                self.console.print(f"  [bold red]✗ {title} failed (exit code {returncode})[/bold red]\n")

        return CommandResult(
            success=success,
            stdout="".join(stdout_chunks),
            stderr="".join(stderr_chunks),
            exit_code=returncode or 0,
            duration_seconds=duration,
        )

    async def install_dependencies(self, project_dir: str) -> CommandResult:
        """Install dependencies based on detected ecosystem."""
        root = find_project_root(project_dir)
        ecosystem = detect_project_ecosystem(root)

        if ecosystem in ("vite_react", "node"):
            return await self.run_command_streamed(
                cmd=["npm", "install"],
                cwd=root,
                title="Installing Node Dependencies (npm install)",
            )
        elif ecosystem == "python":
            req_file = os.path.join(root, "requirements.txt")
            if os.path.exists(req_file):
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
        else:
            return CommandResult(success=True, stdout="No build step defined", stderr="", exit_code=0, duration_seconds=0.0)

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
        Start development server daemon in background, wait for live URL,
        and redirect background output to a log file to avoid TUI prompt pollution.
        """
        root = find_project_root(project_dir)
        ecosystem = detect_project_ecosystem(root)

        if not is_port_available(port):
            raise PortInUseError(f"Port {port} is already in use. Specify a different port with --port.")

        if ecosystem in ("vite_react", "node"):
            cmd = ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", str(port), "--clearScreen=false"]
        elif ecosystem == "python":
            cmd = ["python3", "-m", "http.server", str(port)]
        else:
            cmd = ["python3", "-m", "http.server", str(port)]

        if self.console:
            self.console.print(f"[bold cyan]▶ Spawning Dev Server:[/bold cyan] [dim]{' '.join(cmd)}[/dim]")

        log_file_path = os.path.join(root, ".aztec_server.log")

        # Initialize log file
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"--- Aztec Dev Server Started on Port {port} at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=root,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )

        detected_url = f"http://localhost:{port}"
        ready_event = asyncio.Event()
        ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        url_regex = re.compile(r"(http://localhost:\d+|http://127\.0\.0\.1:\d+|http://0\.0\.0\.0:\d+)")

        async def _monitor_stream():
            assert proc.stdout is not None
            assert proc.stderr is not None

            async def _drain_out():
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    raw_text = line.decode("utf-8", errors="replace")
                    clean_text = ansi_regex.sub("", raw_text)

                    # Write to background log file
                    try:
                        with open(log_file_path, "a", encoding="utf-8") as lf:
                            lf.write(clean_text)
                    except Exception:
                        pass

                    # During startup probe, check for URL and show initial lines
                    if not ready_event.is_set():
                        clean_stripped = clean_text.strip()
                        if clean_stripped and self.console:
                            self.console.print(f"  [dim]{clean_stripped}[/dim]")
                        match = url_regex.search(clean_text)
                        if match:
                            nonlocal detected_url
                            detected_url = match.group(1).replace("0.0.0.0", "localhost")
                            ready_event.set()
                            if on_ready:
                                on_ready(detected_url)

            async def _drain_err():
                while True:
                    line = await proc.stderr.readline()
                    if not line:
                        break
                    raw_text = line.decode("utf-8", errors="replace")
                    clean_text = ansi_regex.sub("", raw_text)
                    try:
                        with open(log_file_path, "a", encoding="utf-8") as lf:
                            lf.write(f"[stderr] {clean_text}")
                    except Exception:
                        pass

            await asyncio.gather(_drain_out(), _drain_err())

        monitor_task = asyncio.create_task(_monitor_stream())

        # Wait up to 5 seconds for Vite/Server startup banner
        try:
            await asyncio.wait_for(ready_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            pass

        if self.console:
            self.console.print(f"\n[bold green]🚀 Live Application Server Running at:[/bold green] [bold underline cyan]{detected_url}[/bold underline cyan]")
            self.console.print(f"[dim]Background logs streaming to {log_file_path} (use /logs to inspect)[/dim]\n")

        return ServerProcess(
            process=proc,
            port=port,
            url=detected_url,
            project_dir=root,
            log_file=log_file_path,
            monitor_task=monitor_task,
        )
