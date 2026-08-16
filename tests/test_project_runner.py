"""
Tests for Aztec Project Scaffolder, Build Runner, Dev Server Daemon, and CLI/TUI commands.
"""

import asyncio
import os
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from rich.console import Console

from aztec_circle.engine.scaffolder import (
    find_project_root,
    detect_project_ecosystem,
    scaffold_project,
)
from aztec_circle.engine.project_runner import (
    ProjectRunner,
    CommandResult,
    ServerProcess,
    PortInUseError,
    is_port_available,
)
from aztec_circle.tui.session import SessionState
from aztec_circle.tui.commands import (
    dispatch_slash_command,
    cmd_build,
    cmd_test,
    cmd_start,
    cmd_stop,
)


def test_find_project_root_flat(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    assert find_project_root(str(tmp_path)) == str(tmp_path)


def test_find_project_root_nested(tmp_path):
    sub = tmp_path / "frontend"
    sub.mkdir()
    (sub / "package.json").write_text("{}", encoding="utf-8")
    assert find_project_root(str(tmp_path)) == str(sub)


def test_detect_project_ecosystem(tmp_path):
    # Vite / React detection
    (tmp_path / "App.tsx").write_text("export const App = () => null;", encoding="utf-8")
    assert detect_project_ecosystem(str(tmp_path)) == "vite_react"

    # Python detection
    py_dir = tmp_path / "py_proj"
    py_dir.mkdir()
    (py_dir / "main.py").write_text("print('hello')", encoding="utf-8")
    assert detect_project_ecosystem(str(py_dir)) == "python"


def test_scaffold_project_vite_react_injects_all_files(tmp_path):
    # Setup a bare component
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "App.tsx").write_text("export default function App() { return <div>Hi</div>; }", encoding="utf-8")

    res = scaffold_project(str(tmp_path))
    assert res.project_type == "vite_react"
    assert "package.json" in res.files_injected
    assert "vite.config.ts" in res.files_injected
    assert "tsconfig.json" in res.files_injected
    assert "index.html" in res.files_injected
    assert "src/main.tsx" in res.files_injected
    assert "src/App.test.tsx" in res.files_injected

    # Verify injected package.json contents
    with open(tmp_path / "package.json", "r", encoding="utf-8") as f:
        pkg = json.load(f)
        assert pkg["dependencies"]["react"] == "^18.3.1"
        assert pkg["devDependencies"]["vite"] == "^5.4.14"


def test_scaffold_project_preserves_existing_files(tmp_path):
    custom_pkg = {"name": "custom-app", "version": "2.0.0"}
    (tmp_path / "package.json").write_text(json.dumps(custom_pkg), encoding="utf-8")
    (tmp_path / "App.tsx").write_text("export const App = () => 1;", encoding="utf-8")

    res = scaffold_project(str(tmp_path))
    assert "package.json" not in res.files_injected

    with open(tmp_path / "package.json", "r", encoding="utf-8") as f:
        pkg = json.load(f)
        assert pkg["name"] == "custom-app"


def test_scaffold_project_python(tmp_path):
    (tmp_path / "engine.py").write_text("def run(): pass", encoding="utf-8")
    res = scaffold_project(str(tmp_path))
    assert res.project_type == "python"
    assert "pyproject.toml" in res.files_injected
    assert os.path.exists(tmp_path / "pyproject.toml")


@pytest.mark.asyncio
async def test_project_runner_install_and_build_node(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"build": "echo built"}}), encoding="utf-8")

    runner = ProjectRunner()
    mock_cmd_result = CommandResult(success=True, stdout="installed", stderr="", exit_code=0, duration_seconds=0.1)

    with patch.object(runner, "run_command_streamed", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = mock_cmd_result

        res_install = await runner.install_dependencies(str(tmp_path))
        assert res_install.success is True
        mock_exec.assert_called_with(
            cmd=["npm", "install"],
            cwd=str(tmp_path),
            title="Installing Node Dependencies (npm install)",
        )

        res_build = await runner.build_project(str(tmp_path))
        assert res_build.success is True
        mock_exec.assert_called_with(
            cmd=["npm", "run", "build"],
            cwd=str(tmp_path),
            title="Building Project (npm run build)",
        )

        res_test = await runner.test_project(str(tmp_path))
        assert res_test.success is True
        mock_exec.assert_called_with(
            cmd=["npm", "test"],
            cwd=str(tmp_path),
            title="Running Test Suite (npm test)",
        )


@pytest.mark.asyncio
async def test_start_dev_server_lifecycle(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"dev": "vite"}}), encoding="utf-8")

    runner = ProjectRunner(console=Console(record=True))

    mock_proc = MagicMock()
    mock_proc.returncode = None
    mock_proc.pid = 99999

    # Simulate stdout streaming Vite banner
    class FakeStream:
        def __init__(self):
            self.lines = [
                "  VITE v5.4.14  ready in 120 ms\n".encode("utf-8"),
                "  ➜  Local:   http://localhost:5173/\n".encode("utf-8"),
                b"",
            ]
            self.idx = 0

        async def readline(self):
            if self.idx < len(self.lines):
                line = self.lines[self.idx]
                self.idx += 1
                return line
            return b""

    mock_proc.stdout = FakeStream()
    mock_proc.stderr = FakeStream()
    mock_proc.terminate = MagicMock()
    mock_proc.wait = AsyncMock(return_value=0)

    with patch("aztec_circle.engine.project_runner.is_port_available", return_value=True), \
         patch("asyncio.create_subprocess_exec", new_callable=AsyncMock, return_value=mock_proc) as mock_exec:

        server_proc = await runner.start_dev_server(str(tmp_path), port=5173)
        assert server_proc.port == 5173
        assert "http://localhost:5173" in server_proc.url
        assert server_proc.log_file is not None
        assert os.path.exists(server_proc.log_file)

        call_args = mock_exec.call_args[0]
        assert "--clearScreen=false" in call_args

        # Test graceful stop
        await server_proc.stop()
        mock_proc.terminate.assert_called_once()


@pytest.mark.asyncio
async def test_start_dev_server_port_in_use(tmp_path):
    runner = ProjectRunner()
    with patch("aztec_circle.engine.project_runner.is_port_available", return_value=False):
        with pytest.raises(PortInUseError) as exc_info:
            await runner.start_dev_server(str(tmp_path), port=5173)
        assert "5173" in str(exc_info.value)


@pytest.mark.asyncio
async def test_tui_slash_build_and_start_commands(tmp_path):
    console = Console(record=True)
    state = SessionState(output_dir=str(tmp_path))

    (tmp_path / "App.tsx").write_text("export default function App() {}", encoding="utf-8")

    with patch("aztec_circle.engine.project_runner.ProjectRunner.install_dependencies", new_callable=AsyncMock) as mock_inst, \
         patch("aztec_circle.engine.project_runner.ProjectRunner.build_project", new_callable=AsyncMock) as mock_bld, \
         patch("aztec_circle.engine.project_runner.ProjectRunner.test_project", new_callable=AsyncMock) as mock_tst, \
         patch("aztec_circle.engine.project_runner.ProjectRunner.start_dev_server", new_callable=AsyncMock) as mock_srv:

        mock_inst.return_value = CommandResult(success=True, stdout="", stderr="", exit_code=0, duration_seconds=0.1)
        mock_bld.return_value = CommandResult(success=True, stdout="", stderr="", exit_code=0, duration_seconds=0.1)
        mock_tst.return_value = CommandResult(success=True, stdout="", stderr="", exit_code=0, duration_seconds=0.1)

        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_srv.return_value = ServerProcess(process=mock_proc, port=5173, url="http://localhost:5173", project_dir=str(tmp_path))

        # /build
        handled_build = await dispatch_slash_command("/build", state, console)
        assert handled_build is True
        mock_inst.assert_called_once()
        mock_bld.assert_called_once()

        # /test
        handled_test = await dispatch_slash_command("/test", state, console)
        assert handled_test is True
        mock_tst.assert_called_once()

        # /start
        handled_start = await dispatch_slash_command("/start", state, console)
        assert handled_start is True
        assert state.active_server is not None

        # /stop
        state.active_server.stop = AsyncMock()
        handled_stop = await dispatch_slash_command("/stop", state, console)
        assert handled_stop is True
        assert state.active_server is None
