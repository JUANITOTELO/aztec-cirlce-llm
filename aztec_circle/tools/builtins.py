"""
Built-in tools: filesystem inspection/mutation (root-confined), git reads,
shell execution, project test/build, and the self-extension meta-tools
(tool_list / tool_create / tool_remove) that let the circle grow its own
toolset safely.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from aztec_circle.tools.base import (
    Handler,
    ParamSpec,
    ParamType,
    SafetyClass,
    ToolContext,
    ToolResult,
    ToolSpec,
)
from aztec_circle.tools.registry import ToolRegistry


async def _run_capture(cmd: List[str], ctx: ToolContext, timeout_s: float, cap: int) -> ToolResult:
    import asyncio

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(ctx.root_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return ToolResult(ok=False, error=f"timed out after {timeout_s}s", exit_code=-1)
    out = stdout.decode(errors="replace")
    truncated = len(out) > cap
    return ToolResult(ok=(proc.returncode == 0), output=out[:cap], exit_code=proc.returncode or 0, truncated=truncated)


# ── Filesystem tools ─────────────────────────────────────────────────────────

async def fs_read(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    try:
        path = ctx.confine(args["path"])
    except PermissionError as exc:
        return ToolResult(ok=False, error=str(exc))
    if not path.exists():
        return ToolResult(ok=False, error=f"not found: {args['path']}")
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except IsADirectoryError:
        return ToolResult(ok=False, error=f"is a directory: {args['path']}")
    offset = int(args.get("offset", 0) or 0)
    limit = int(args.get("limit", 400) or 400)
    lines = text.splitlines()
    window = lines[offset:offset + limit]
    body = "\n".join(f"{offset + i + 1}|{line}" for i, line in enumerate(window))
    return ToolResult(ok=True, output=f"{len(lines)} total lines\n{body}")


async def fs_write(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    try:
        path = ctx.confine(args["path"])
    except PermissionError as exc:
        return ToolResult(ok=False, error=str(exc))
    content = args["content"]
    mode = str(args.get("mode", "overwrite"))
    try:
        if mode == "append" and path.exists():
            existing = path.read_text(encoding="utf-8", errors="replace")
            path.write_text(existing + content, encoding="utf-8")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        size = path.stat().st_size
        return ToolResult(ok=True, output=f"wrote {size} bytes to {path.relative_to(ctx.root_path)}")
    except OSError as exc:
        return ToolResult(ok=False, error=str(exc))


async def fs_list(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    target = args.get("path", ".")
    try:
        path = ctx.confine(target)
    except PermissionError as exc:
        return ToolResult(ok=False, error=str(exc))
    if not path.is_dir():
        return ToolResult(ok=False, error=f"not a directory: {target}")
    entries = sorted(path.iterdir(), key=lambda p: p.name)
    rows = []
    for entry in entries[:500]:
        kind = "dir " if entry.is_dir() else "file"
        size = entry.stat().st_size if entry.is_file() else ""
        rows.append(f"{kind} {size:>10}  {entry.name}")
    return ToolResult(ok=True, output="\n".join(rows) or "(empty directory)")


async def fs_search(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    """Regex search across text files under the project root."""
    import re

    try:
        pattern = re.compile(args["pattern"])
    except re.error as exc:
        return ToolResult(ok=False, error=f"bad regex: {exc}")
    glob_filter = args.get("glob") or "**/*"
    root = ctx.root_path
    hits: List[str] = []
    skipped = 0
    try:
        candidates = list(root.glob(glob_filter))
    except ValueError as exc:
        return ToolResult(ok=False, error=str(exc))
    skip_dirs = {".git", "node_modules", ".venv", "venv", "__pycache__", ".aztec", "dist", "build"}
    for file_path in candidates:
        if not file_path.is_file():
            continue
        if any(part in skip_dirs for part in file_path.parts):
            skipped += 1
            continue
        try:
            if file_path.stat().st_size > 512_000:
                continue
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = file_path.relative_to(root)
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                hits.append(f"{rel}:{lineno}: {line.strip()[:160]}")
                if len(hits) >= 200:
                    break
        if len(hits) >= 200:
            break
    header = f"{len(hits)} match(es)" + (f" (skipped dirs: {skipped})" if skipped else "")
    return ToolResult(ok=bool(hits), output="\n".join([header] + hits))


# ── Git read-only tools ──────────────────────────────────────────────────────

async def git_status(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    return await _run_capture(["git", "status", "--short", "-uno"], ctx, 15.0, 20_000)


async def git_diff(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    base = args.get("base") or "HEAD"
    return await _run_capture(["git", "diff", base], ctx, 30.0, 40_000)


async def git_log(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    n = int(args.get("limit", 10))
    return await _run_capture(
        ["git", "log", "--oneline", f"-n{n}"], ctx, 15.0, 10_000
    )


# ── Project tools ────────────────────────────────────────────────────────────

async def shell_run(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    from aztec_circle.tools.registry import _run_shell
    return await _run_shell(str(args["command"]), ctx, float(args.get("timeout_s", 120)), 20_000)


async def proj_inspect(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    """Detect project type and summarize its shape — the 'look around' tool."""
    root = ctx.root_path
    markers = {
        "package.json": "node/js",
        "pyproject.toml": "python",
        "requirements.txt": "python",
        "go.mod": "go",
        "Cargo.toml": "rust",
        "composer.json": "php",
        "docker-compose.yml": "docker",
        "Makefile": "make",
    }
    found = [label for marker, label in markers.items() if (root / marker).exists()]
    src_summary: List[str] = [f"root: {root}", "type: " + (", ".join(found) or "unknown")]
    src_dir = root / "src"
    if src_dir.is_dir():
        code_files = [
            p.name for p in list(src_dir.rglob("*"))[:400]
            if p.suffix in (".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".php")
        ]
        src_summary.append(f"src/ code files ({len(code_files)}): {', '.join(sorted(code_files)[:25])}")
    tests = [p.name for p in root.glob("test*") if p.exists()]
    if tests:
        src_summary.append(f"tests: {', '.join(tests)}")
    return ToolResult(ok=True, output="\n".join(src_summary))


async def proj_test(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    root = ctx.root_path
    if (root / "package.json").exists():
        cmd = ["npm", "test", "--", "--run"] if (root / "node_modules").exists() else None
        if cmd is None:
            return ToolResult(ok=False, error="node_modules missing — run install first")
        from aztec_circle.tools.base import render_template  # noqa: F401
        return await _run_capture(cmd, ctx, timeout_s=float(args.get("timeout_s", 300)), cap=40_000)
    if any((root / f).exists() for f in ("pytest.ini", "pyproject.toml", "setup.py")) or list(root.glob("test_*.py")) or (root / "tests").is_dir():
        pytest_args = ["python", "-m", "pytest", "-q"]
        if args.get("path"):
            pytest_args.append(str(args["path"]))
        return await _run_capture(pytest_args, ctx, timeout_s=float(args.get("timeout_s", 300)), cap=40_000)
    return ToolResult(ok=False, error="no recognized test suite (npm/pytest)")


# ── Self-extension meta-tools ────────────────────────────────────────────────

async def tool_create(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    registry = get_registry_for(ctx)
    params_raw = args.get("params_json") or "{}"
    try:
        params_data = json.loads(params_raw)
        params = {
            name: ParamSpec(name=name, **(spec if isinstance(spec, dict) else {"type": str(spec)}))
            for name, spec in params_data.items()
        }
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return ToolResult(ok=False, error=f"invalid params_json: {exc}")

    template = args.get("template")
    if not template:
        return ToolResult(ok=False, error="'template' is required (a shell command with {placeholder} tokens)")

    spec = ToolSpec(
        name=str(args["name"]),
        description=str(args.get("description") or f"custom tool {args['name']}"),
        safety=SafetyClass(str(args.get("safety") or "mutating")),
        params=params,
        template=template,
        timeout_s=float(args.get("timeout_s", 60)),
    )
    scope = str(args.get("scope", "project"))
    path = registry.save_tool(spec, scope=scope)
    return ToolResult(ok=True, output=f"tool '{spec.name}' saved to {path} (scope={scope}); invoke via aztec tool run {spec.name}")


def get_registry_for(ctx: ToolContext) -> ToolRegistry:
    from aztec_circle.tools.registry import register_builtins
    reg = ToolRegistry(project_root=ctx.project_root)
    register_builtins(reg)
    # Re-load saved tools so newly created ones resolve immediately.
    reg.load_saved_tools()
    return reg


async def tool_remove(args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
    registry = get_registry_for(ctx)
    removed = registry.remove_tool(str(args["name"]), scope=args.get("scope"))
    if removed:
        return ToolResult(ok=True, output=f"removed tool '{args['name']}'")
    return ToolResult(ok=False, error=f"'{args['name']}' is not a saved custom tool")


# ── Registry export ──────────────────────────────────────────────────────────

BUILTIN_TOOLS: List[Tuple[ToolSpec, Handler]] = [
    (
        ToolSpec(
            name="fs_read",
            description="Read a text file (line-numbered) inside the project",
            safety=SafetyClass.READ_ONLY,
            params={
                "path": ParamSpec(name="path", description="project-relative file path"),
                "offset": ParamSpec(name="offset", type=ParamType.INT, required=False, default="0"),
                "limit": ParamSpec(name="limit", type=ParamType.INT, required=False, default="400"),
            },
        ),
        fs_read,
    ),
    (
        ToolSpec(
            name="fs_write",
            description="Write/append a file inside the project",
            safety=SafetyClass.MUTATING,
            params={
                "path": ParamSpec(name="path", description="project-relative file path"),
                "content": ParamSpec(name="content", description="file contents"),
                "mode": ParamSpec(name="mode", required=False, default="overwrite", pattern="^(overwrite|append)$"),
            },
        ),
        fs_write,
    ),
    (
        ToolSpec(
            name="fs_list",
            description="List a directory inside the project",
            safety=SafetyClass.READ_ONLY,
            params={"path": ParamSpec(name="path", required=False, default=".")},
        ),
        fs_list,
    ),
    (
        ToolSpec(
            name="fs_search",
            description="Regex-search text files under the project",
            safety=SafetyClass.READ_ONLY,
            params={
                "pattern": ParamSpec(name="pattern", description="regex"),
                "glob": ParamSpec(name="glob", required=False, default="**/*"),
            },
        ),
        fs_search,
    ),
    (
        ToolSpec(
            name="git_status",
            description="Short git status of the project (tracked changes)",
            safety=SafetyClass.READ_ONLY,
            params={},
        ),
        git_status,
    ),
    (
        ToolSpec(
            name="git_diff",
            description="Git diff against a base ref (default HEAD)",
            safety=SafetyClass.READ_ONLY,
            params={"base": ParamSpec(name="base", required=False)},
        ),
        git_diff,
    ),
    (
        ToolSpec(
            name="git_log",
            description="Recent commit history",
            safety=SafetyClass.READ_ONLY,
            params={"limit": ParamSpec(name="limit", type=ParamType.INT, required=False, default="10")},
        ),
        git_log,
    ),
    (
        ToolSpec(
            name="shell_run",
            description="Run an arbitrary shell command in the project root",
            safety=SafetyClass.DANGEROUS,
            timeout_s=180.0,
            output_cap_chars=20_000,
            params={
                "command": ParamSpec(name="command", description="shell command string"),
                "timeout_s": ParamSpec(name="timeout_s", type=ParamType.FLOAT, required=False, default="120"),
            },
        ),
        shell_run,
    ),
    (
        ToolSpec(
            name="proj_inspect",
            description="Identify project type, structure, and entry points",
            safety=SafetyClass.READ_ONLY,
            params={},
        ),
        proj_inspect,
    ),
    (
        ToolSpec(
            name="proj_test",
            description="Run the project's test suite (npm test / pytest)",
            safety=SafetyClass.MUTATING,
            timeout_s=330.0,
            params={
                "path": ParamSpec(name="path", required=False),
                "timeout_s": ParamSpec(name="timeout_s", type=ParamType.FLOAT, required=False, default="300"),
            },
        ),
        proj_test,
    ),
    (
        ToolSpec(
            name="tool_create",
            description="Create and persist a new custom shell-template tool",
            safety=SafetyClass.MUTATING,
            params={
                "name": ParamSpec(name="name", pattern=r"^[a-z][a-z0-9_]{2,40}$"),
                "template": ParamSpec(name="template", description='shell command with {placeholders}, e.g. "wc -l {file}"'),
                "description": ParamSpec(name="description", required=False),
                "params_json": ParamSpec(name="params_json", required=False, description='{"file": {"type":"str"}}'),
                "safety": ParamSpec(name="safety", required=False, default="mutating", pattern="^(read_only|mutating|dangerous)$"),
                "scope": ParamSpec(name="scope", required=False, default="project", pattern="^(project|global)$"),
                "timeout_s": ParamSpec(name="timeout_s", type=ParamType.FLOAT, required=False, default="60"),
            },
        ),
        tool_create,
    ),
    (
        ToolSpec(
            name="tool_remove",
            description="Remove a saved custom tool",
            safety=SafetyClass.MUTATING,
            params={
                "name": ParamSpec(name="name"),
                "scope": ParamSpec(name="scope", required=False, pattern="^(project|global)$"),
            },
        ),
        tool_remove,
    ),
]
