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
import json
import subprocess
from dataclasses import dataclass, field
from typing import Callable, List, Optional
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
    """Manages an active background development server or multi-service cluster."""
    process: asyncio.subprocess.Process
    port: int
    url: str
    project_dir: str
    backend_process: Optional[asyncio.subprocess.Process] = None
    backend_port: Optional[int] = None
    backend_url: Optional[str] = None
    log_file: Optional[str] = None
    monitor_task: Optional[asyncio.Task] = None

    async def stop(self) -> None:
        """Gracefully terminate all dev server processes and their process groups."""
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
        
        for p in [self.process, self.backend_process]:
            if p and p.returncode is None:
                try:
                    import signal
                    try:
                        pgid = os.getpgid(p.pid)
                        os.killpg(pgid, signal.SIGTERM)
                    except Exception:
                        p.terminate()
                    await asyncio.wait_for(p.wait(), timeout=2.0)
                except Exception:
                    try:
                        import signal
                        try:
                            pgid = os.getpgid(p.pid)
                            os.killpg(pgid, signal.SIGKILL)
                        except Exception:
                            p.kill()
                        await p.wait()
                    except Exception:
                        pass


def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is open for binding."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        res = s.connect_ex((host, port))
        return res != 0


def find_free_port(start_port: int, max_offset: int = 50, host: str = "127.0.0.1") -> int:
    """Find the next available TCP port starting from start_port."""
    port = start_port
    while not is_port_available(port, host) and port < start_port + max_offset:
        port += 1
    return port


def free_ports(ports: List[int]) -> List[int]:
    """
    Identify and terminate processes listening on the given TCP ports.
    Returns the list of ports that were freed.
    """
    freed: List[int] = []
    for port in ports:
        try:
            # Check via lsof
            res = subprocess.run(["lsof", "-t", f"-i:{port}"], capture_output=True, text=True)
            pids = [int(p.strip()) for p in res.stdout.split() if p.strip().isdigit()]
            if not pids:
                # Check via fuser
                res2 = subprocess.run(["fuser", f"{port}/tcp"], capture_output=True, text=True)
                pids = [int(p.strip()) for p in res2.stdout.split() if p.strip().isdigit()]

            for pid in pids:
                try:
                    import signal
                    os.kill(pid, signal.SIGTERM)
                    time.sleep(0.05)
                    os.kill(pid, signal.SIGKILL)
                except Exception:
                    pass
            if pids:
                freed.append(port)
        except Exception:
            pass
    return freed


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

    async def run_shell_command_streamed(
        self,
        cmd_str: str,
        cwd: str,
        title: str = "Console Command",
    ) -> CommandResult:
        """Execute shell command string asynchronously with streaming Rich output and shell feature support (pipes, redirects, env vars)."""
        if self.console:
            self.console.print(f"[bold cyan]▶ {title}:[/bold cyan] [bold yellow]{cmd_str}[/bold yellow] [dim](cwd: {cwd})[/dim]")

        start_time = time.time()
        proc = await asyncio.create_subprocess_shell(
            cmd_str,
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
                self.console.print(f"  [bold green]✓ {title} completed successfully ({duration:.2f}s)[/bold green]\n")
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
        """Execute project test suites across all tiers (Frontend, Backend, Types/Proofs)."""
        root = find_project_root(project_dir)
        ecosystem = detect_project_ecosystem(root)

        results: List[CommandResult] = []

        # 1. Check PHP backend tests
        php_test_files = [
            os.path.join(root, "backend", "test_backend.php"),
            os.path.join(root, "test_backend.php"),
            os.path.join(root, "tests", "test_backend.php"),
        ]
        for ptf in php_test_files:
            if os.path.exists(ptf):
                rel = os.path.relpath(ptf, root)
                res = await self.run_command_streamed(
                    cmd=["php", rel],
                    cwd=root,
                    title=f"Running PHP Backend Tests (php {rel})",
                )
                results.append(res)
                break
        else:
            if os.path.exists(os.path.join(root, "vendor", "bin", "phpunit")):
                res = await self.run_command_streamed(
                    cmd=["./vendor/bin/phpunit"],
                    cwd=root,
                    title="Running PHPUnit Test Suite",
                )
                results.append(res)

        # 2. Check Node / React / Vitest tests
        pkg_path = os.path.join(root, "package.json")
        if os.path.exists(pkg_path):
            res = await self.run_command_streamed(
                cmd=["npm", "test"],
                cwd=root,
                title="Running Test Suite (npm test)",
            )
            results.append(res)

        # 3. Check Python tests
        if os.path.exists(os.path.join(root, "pyproject.toml")) or os.path.exists(os.path.join(root, "requirements.txt")) or any(f.endswith(".py") for f in os.listdir(root) if os.path.isfile(os.path.join(root, f))):
            if ecosystem not in ("php_react", "vite_react") or os.path.exists(os.path.join(root, "tests")):
                if os.path.exists(os.path.join(root, "tests")) or os.path.exists(os.path.join(root, "test")):
                    res = await self.run_command_streamed(
                        cmd=["pytest"],
                        cwd=root,
                        title="Running Python Test Suite (pytest)",
                    )
                    results.append(res)

        # 4. Check Lean 4 proofs
        if os.path.exists(os.path.join(root, "lakefile.lean")):
            res = await self.run_command_streamed(
                cmd=["lake", "build"],
                cwd=root,
                title="Verifying Lean 4 Formal Proofs (lake build)",
            )
            results.append(res)

        if not results:
            return CommandResult(success=True, stdout="No test suite discovered in project", stderr="", exit_code=0, duration_seconds=0.0)

        all_success = all(r.success for r in results)
        merged_stdout = "\n".join(r.stdout for r in results if r.stdout)
        merged_stderr = "\n".join(r.stderr for r in results if r.stderr)
        max_exit = max(r.exit_code for r in results)
        total_duration = sum(r.duration_seconds for r in results)

        return CommandResult(
            success=all_success,
            stdout=merged_stdout,
            stderr=merged_stderr,
            exit_code=max_exit,
            duration_seconds=total_duration,
        )

    async def start_dev_server(
        self,
        project_dir: str,
        port: int = 5173,
        backend_port: int = 8000,
        on_ready: Optional[Callable[[str], None]] = None,
    ) -> ServerProcess:
        """
        Start development server daemon in background, wait for live URL,
        orchestrating multi-service hybrid fullstack projects cleanly.
        """
        root = find_project_root(project_dir)
        ecosystem = detect_project_ecosystem(root)

        if not is_port_available(port):
            frontend_port = find_free_port(port)
            if not is_port_available(frontend_port):
                raise PortInUseError(f"Port {port} is already in use. Specify a different port with --port.")
            if self.console:
                self.console.print(f"[yellow]⚡ Notice: Port {port} is in use; automatically bound frontend to free port {frontend_port}[/yellow]")
        else:
            frontend_port = port

        log_file_path = os.path.join(root, ".aztec_server.log")
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"--- Aztec Dev Server Started at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

        backend_proc: Optional[asyncio.subprocess.Process] = None
        actual_backend_port: Optional[int] = None
        backend_url: Optional[str] = None

        # Hybrid fullstack: Spawn Backend API Server first
        if ecosystem == "php_react":
            actual_backend_port = find_free_port(backend_port)
            backend_url = f"http://127.0.0.1:{actual_backend_port}"
            
            php_entry = "backend/index.php" if os.path.exists(os.path.join(root, "backend", "index.php")) else "index.php"
            backend_cmd = ["php", "-S", f"127.0.0.1:{actual_backend_port}", php_entry]

            if self.console:
                self.console.print(f"[bold cyan]▶ Spawning Backend API Server (PHP):[/bold cyan] [dim]{' '.join(backend_cmd)}[/dim]")

            backend_proc = await asyncio.create_subprocess_exec(
                *backend_cmd,
                cwd=root,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )

        elif ecosystem == "python_react":
            actual_backend_port = find_free_port(backend_port)
            backend_url = f"http://127.0.0.1:{actual_backend_port}"
            py_entry = "server.py" if os.path.exists(os.path.join(root, "server.py")) else ("app.py" if os.path.exists(os.path.join(root, "app.py")) else "-m http.server")
            backend_cmd = ["python3", py_entry] if not py_entry.startswith("-m") else ["python3", "-m", "http.server", str(actual_backend_port)]

            if self.console:
                self.console.print(f"[bold cyan]▶ Spawning Backend API Server (Python):[/bold cyan] [dim]{' '.join(backend_cmd)}[/dim]")

            backend_proc = await asyncio.create_subprocess_exec(
                *backend_cmd,
                cwd=root,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                start_new_session=True,
            )

        # Spawn Frontend / Primary Server
        if ecosystem in ("vite_react", "php_react", "python_react", "lean4_react", "node"):
            cmd = ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", str(frontend_port), "--clearScreen=false"]
        elif ecosystem == "php":
            cmd = ["php", "-S", f"0.0.0.0:{frontend_port}"]
        else:
            cmd = ["python3", "-m", "http.server", str(frontend_port)]

        if self.console:
            self.console.print(f"[bold cyan]▶ Spawning Frontend Dev Server:[/bold cyan] [dim]{' '.join(cmd)}[/dim]")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=root,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )

        detected_url = f"http://localhost:{frontend_port}"
        ready_event = asyncio.Event()
        ansi_regex = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        url_regex = re.compile(r"(http://localhost:\d+|http://127\.0\.0\.1:\d+|http://0\.0\.0\.0:\d+)")

        async def _monitor_stream(p: asyncio.subprocess.Process, label: str = "app"):
            async def _drain_out():
                while True:
                    line = await p.stdout.readline()
                    if not line:
                        break
                    raw_text = line.decode("utf-8", errors="replace")
                    clean_text = ansi_regex.sub("", raw_text)

                    try:
                        with open(log_file_path, "a", encoding="utf-8") as lf:
                            lf.write(f"[{label}] {clean_text}")
                    except Exception:
                        pass

                    if not ready_event.is_set() and label == "frontend":
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
                    line = await p.stderr.readline()
                    if not line:
                        break
                    raw_text = line.decode("utf-8", errors="replace")
                    clean_text = ansi_regex.sub("", raw_text)
                    try:
                        with open(log_file_path, "a", encoding="utf-8") as lf:
                            lf.write(f"[{label}-stderr] {clean_text}")
                    except Exception:
                        pass

            await asyncio.gather(_drain_out(), _drain_err())

        tasks = [_monitor_stream(proc, "frontend")]
        if backend_proc:
            tasks.append(_monitor_stream(backend_proc, "backend"))

        async def _run_all_monitors():
            await asyncio.gather(*tasks)

        monitor_task = asyncio.create_task(_run_all_monitors())

        # Wait up to 5 seconds for Frontend startup banner
        try:
            await asyncio.wait_for(ready_event.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            pass

        if self.console:
            self.console.print(f"\n[bold green]🚀 Live Application Server Running at:[/bold green] [bold underline cyan]{detected_url}[/bold underline cyan]")
            if backend_url:
                self.console.print(f"[bold green]🔗 Backend REST API Running at:[/bold green] [bold underline magenta]{backend_url}[/bold underline magenta]")
            self.console.print(f"[dim]Background logs streaming to {log_file_path} (use /logs to inspect)[/dim]\n")

        return ServerProcess(
            process=proc,
            port=frontend_port,
            url=detected_url,
            project_dir=root,
            backend_process=backend_proc,
            backend_port=actual_backend_port,
            backend_url=backend_url,
            log_file=log_file_path,
            monitor_task=monitor_task,
        )

