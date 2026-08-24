"""
Tests for the tool subsystem: spec validation, injection-safe templates,
project-root confinement, confirmation gates, audit trail, persistence,
and the tool_create -> run self-extension loop.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from aztec_circle.tools import ToolContext, ToolSpec, get_registry
from aztec_circle.tools.base import ParamSpec, ParamType, SafetyClass
from aztec_circle.tools.base import render_template


# ── Spec validation & template safety ────────────────────────────────────────

def test_coerce_args_types_and_unknowns():
    spec = ToolSpec(
        name="demo",
        description="d",
        params={
            "count": ParamSpec(name="count", type=ParamType.INT),
            "rate": ParamSpec(name="rate", type=ParamType.FLOAT, required=False),
            "flag": ParamSpec(name="flag", type=ParamType.BOOL, required=False),
        },
    )
    coerced = spec.coerce_args({"count": "7", "rate": "0.5", "flag": "true"})
    assert coerced == {"count": 7, "rate": 0.5, "flag": True}

    with pytest.raises(ValueError, match="missing required"):
        spec.coerce_args({})
    with pytest.raises(ValueError, match="unknown argument"):
        spec.coerce_args({"count": 1, "bogus": 2})
    with pytest.raises(ValueError, match="must be int"):
        spec.coerce_args({"count": "abc"})


def test_pattern_validation_blocks_bad_input():
    spec = ToolSpec(
        name="patted",
        description="d",
        params={"ref": ParamSpec(name="ref", pattern=r"^[a-z0-9-]+$")},
    )
    assert spec.coerce_args({"ref": "abc-123"}) == {"ref": "abc-123"}
    with pytest.raises(ValueError, match="pattern"):
        spec.coerce_args({"ref": "abc; rm -rf /"})


def test_template_rendering_is_injection_safe():
    import shlex

    hostile = "a.txt'; rm -rf / #"
    rendered = render_template("wc -l {file}", {"file": hostile})
    # The payload must survive as a SINGLE literal argument — shlex.split must
    # round-trip it exactly, proving no shell metacharacters escaped quoting.
    assert shlex.split(rendered) == ["wc", "-l", hostile]


def test_name_and_param_patterns_enforced_by_pydantic():
    with pytest.raises(Exception):
        ToolSpec(name="BadName", description="x")
    with pytest.raises(Exception):
        ParamSpec(name="1bad")


# ── Execution: confinement, gates, audit ─────────────────────────────────────

@pytest.fixture
def project(tmp_path):
    import subprocess

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hello')\n")
    (tmp_path / "README.md").write_text("# demo\nsearchme token\n")
    # Real git repo so git tools behave.
    env_args = ["-c", "user.name=t", "-c", "user.email=t@t"]
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", *env_args, "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", *env_args, "commit", "-qm", "init"], cwd=tmp_path, check=True, capture_output=True)
    return tmp_path


def make_ctx(project, auto_approve=True, confirm_cb=None):
    return ToolContext(project_root=str(project), auto_approve=auto_approve, confirm_cb=confirm_cb)


@pytest.mark.asyncio
async def test_fs_read_lists_and_search(project):
    reg = get_registry(str(project))
    read = await reg.execute("fs_read", {"path": "src/app.py"}, make_ctx(project))
    assert read.ok and "print('hello')" in read.output

    listing = await reg.execute("fs_list", {"path": "."}, make_ctx(project))
    assert "src" in listing.output and "README.md" in listing.output

    search = await reg.execute("fs_search", {"pattern": r"token"}, make_ctx(project))
    assert "README.md" in search.output


@pytest.mark.asyncio
async def test_fs_tools_confined_to_project_root(project):
    reg = get_registry(str(project))
    ctx = make_ctx(project)
    for tool, args in (
        ("fs_read", {"path": "/etc/passwd"}),
        ("fs_read", {"path": "../../etc/passwd"}),
        ("fs_write", {"path": "../escape.txt", "content": "nope"}),
    ):
        res = await reg.execute(tool, args, ctx)
        assert not res.ok
        assert "escapes project root" in res.error


@pytest.mark.asyncio
async def test_dangerous_tool_requires_confirmation_gate(project):
    reg = get_registry(str(project))

    approved_calls = []

    async def confirm(tool_name, safety):
        approved_calls.append((tool_name, safety))
        return False  # deny

    ctx = ToolContext(project_root=str(project), auto_approve=False, confirm_cb=confirm)
    res = await reg.execute("shell_run", {"command": "echo hi"}, ctx)
    assert not res.ok and "not approved" in res.error
    assert approved_calls == [("shell_run", SafetyClass.DANGEROUS)]


@pytest.mark.asyncio
async def test_shell_run_executes_and_captures(project):
    reg = get_registry(str(project))
    res = await reg.execute("shell_run", {"command": "echo aztec-tools-work"}, make_ctx(project))
    assert res.ok and "aztec-tools-work" in res.output


@pytest.mark.asyncio
async def test_mutating_write_requires_gate_but_runs_when_auto(project):
    reg = get_registry(str(project))
    ctx = make_ctx(project)  # auto_approve=True simulates an approved session
    res = await reg.execute("fs_write", {"path": "out/new.txt", "content": "data"}, ctx)
    assert res.ok
    assert (project / "out" / "new.txt").read_text() == "data"


@pytest.mark.asyncio
async def test_audit_trail_written(project):
    reg = get_registry(str(project))
    await reg.execute("git_log", {"limit": "2"}, make_ctx(project))
    audit = Path(project) / ".aztec" / "tool_audit.jsonl"
    assert audit.exists()
    entries = [json.loads(line) for line in audit.read_text().splitlines()]
    assert any(e["tool"] == "git_log" and e["ok"] for e in entries)


@pytest.mark.asyncio
async def test_output_cap_and_timeout_paths(project):
    reg = get_registry(str(project))
    big = await reg.execute("shell_run", {"command": "yes aztec | head -50000"}, make_ctx(project))
    assert len(big.output) <= 20_000 + 10  # capped

    slow = await reg.execute("shell_run", {"command": "sleep 5", "timeout_s": "0.3"}, make_ctx(project))
    assert not slow.ok and "timed out" in slow.error.lower()


@pytest.mark.asyncio
async def test_unknown_tool_and_bad_args(project):
    reg = get_registry(str(project))
    unknown = await reg.execute("does_not_exist", {}, make_ctx(project))
    assert not unknown.ok and "unknown tool" in unknown.error

    bad = await reg.execute("fs_read", {"nonsense": 1}, make_ctx(project))
    assert not bad.ok and "invalid arguments" in bad.error


# ── Self-extension: create → persist → reload → run ─────────────────────────

@pytest.mark.asyncio
async def test_tool_create_persists_and_runs(project, monkeypatch):
    monkeypatch.setattr("aztec_circle.tools.registry.GLOBAL_TOOLS_DIR", Path(project) / "globaltools")
    reg = get_registry(str(project))
    ctx = make_ctx(project)

    created = await reg.execute("tool_create", {
        "name": "line_count",
        "template": "wc -l {file}",
        "description": "Count lines in a file",
        "params_json": json.dumps({"file": {"type": "str"}}),
        "safety": "read_only",
        "scope": "project",
    }, ctx)
    assert created.ok, created.error

    # Fresh registry picks it up from disk.
    fresh = get_registry(str(project)) if False else None
    from aztec_circle.tools.registry import ToolRegistry, register_builtins
    reloaded = ToolRegistry(project_root=str(project))
    register_builtins(reloaded)
    reloaded.load_saved_tools()
    assert reloaded.get("line_count") is not None
    assert reloaded.source_of("line_count") == "project"

    run = await reloaded.execute("line_count", {"file": "src/app.py"}, make_ctx(project))
    assert run.ok and "1" in run.output.split()[0]

    # Remove it.
    removed = reloaded.remove_tool("line_count", scope="project")
    assert removed
    assert not (Path(project) / ".aztec" / "tools" / "line_count.json").exists()


def test_project_scope_overrides_global(monkeypatch, tmp_path):
    global_dir = tmp_path / "g"
    proj_dir = tmp_path / "p" / ".aztec" / "tools"
    global_dir.mkdir(parents=True)
    proj_dir.mkdir(parents=True)

    spec_data = {"name": "dupe_tool", "description": "global version", "template": "echo global"}
    (global_dir / "dupe_tool.json").write_text(json.dumps(spec_data))
    spec_data2 = {"name": "dupe_tool", "description": "project version", "template": "echo project"}
    (proj_dir / "dupe_tool.json").write_text(json.dumps(spec_data2))

    monkeypatch.setattr("aztec_circle.tools.registry.GLOBAL_TOOLS_DIR", global_dir)
    from aztec_circle.tools.registry import ToolRegistry, register_builtins
    reg = ToolRegistry(project_root=str(tmp_path / "p"))
    register_builtins(reg)
    reg.load_saved_tools()
    assert reg.source_of("dupe_tool") == "project"
    dupe = reg.get("dupe_tool")
    assert dupe is not None and dupe.description == "project version"


# ── TUI surface ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_tui_tool_command_list_run_create_remove(tmp_path, monkeypatch):
    from rich.console import Console
    from aztec_circle.tui.commands import dispatch_slash_command
    from aztec_circle.tui.session import SessionState

    monkeypatch.setattr("aztec_circle.tools.registry.GLOBAL_TOOLS_DIR", Path(tmp_path) / "gt")

    state = SessionState()
    state.output_dir = str(tmp_path)  # operate inside the temp project

    console = Console(record=True, width=200)
    await dispatch_slash_command("/tool list", state, console)
    text = console.export_text()
    assert "fs_search" in text and "shell_run" in text

    console = Console(record=True, width=200)
    await dispatch_slash_command(f"/tool create count_words --template 'wc -w {{file}}' --desc 'word counter' --safety read_only", state, console)
    saved_text = console.export_text()
    assert "saved" in saved_text.lower()

    # Run the freshly created custom tool.
    console = Console(record=True, width=200)
    (tmp_path / "sample.txt").write_text("one two three four\n")
    await dispatch_slash_command("/tool run count_words file=sample.txt", state, console)
    run_text = console.export_text()
    assert "4" in run_text  # wc -w output

    console = Console(record=True, width=200)
    await dispatch_slash_command("/tool remove count_words", state, console)
    assert "Removed" in console.export_text()


# ── CLI surface ──────────────────────────────────────────────────────────────

def test_cli_tool_group_list_run_create_remove(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from unittest.mock import patch as mock_patch

    from aztec_circle.cli import app

    monkeypatch.setattr("aztec_circle.tools.registry.GLOBAL_TOOLS_DIR", tmp_path / "gt")
    runner = CliRunner()

    res = runner.invoke(app, ["tool", "list", "--path", str(tmp_path)])
    assert res.exit_code == 0 and "fs_search" in res.stdout

    res = runner.invoke(app, [
        "tool", "create", "upper_file",
        "--template", "cat {file} | tr '[:lower:]' '[:upper:]'",
        "--desc", "uppercase a file",
        "--safety", "read_only",
        "--param", "file:str",
        "--path", str(tmp_path),
    ])
    assert res.exit_code == 0 and "created" in res.stdout.lower()

    (tmp_path / "hello.txt").write_text("hello tools\n")
    res = runner.invoke(app, [
        "tool", "run", "upper_file", f"file={tmp_path / 'hello.txt'}", "--yes",
    ])
    # fs confinement: absolute path outside root should fail cleanly.
    assert "escapes project root" in res.stdout or res.exit_code != 0

    res = runner.invoke(app, [
        "tool", "run", "upper_file", "file=hello.txt", "--yes", "--path", str(tmp_path),
    ])
    assert res.exit_code == 0 and "HELLO TOOLS" in res.stdout

    res = runner.invoke(app, ["tool", "remove", "upper_file", "--path", str(tmp_path)])
    assert res.exit_code == 0 and "Removed" in res.stdout
