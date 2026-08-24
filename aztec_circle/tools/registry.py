"""
ToolRegistry: registration, validation, safety gates, execution, audit trail,
and persistent self-extension (project + global tool directories).
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import structlog

from aztec_circle.tools.base import (
    Handler,
    SafetyClass,
    ToolContext,
    ToolResult,
    ToolSpec,
    confirm_or_raise,
    render_template,
)

log = structlog.get_logger(__name__)

GLOBAL_TOOLS_DIR = Path("~/.aztec/tools.d").expanduser()
PROJECT_TOOLS_DIR = ".aztec/tools"
AUDIT_FILE = ".aztec/tool_audit.jsonl"


class ToolRegistry:
    def __init__(self, project_root: str = ".", load_saved: bool = True):
        self.project_root = str(Path(project_root).expanduser().resolve())
        self._tools: Dict[str, ToolSpec] = {}
        self._handlers: Dict[str, Handler] = {}
        self._sources: Dict[str, str] = {}  # name -> "builtin" | "project" | "global"
        if load_saved:
            self.load_saved_tools()

    # ── Registration ─────────────────────────────────────────────────────
    def register(self, spec: ToolSpec, handler: Optional[Handler] = None, source: str = "builtin") -> None:
        if spec.name in self._tools and source != "builtin":
            existing_source = self._sources.get(spec.name, "builtin")
            if existing_source == "builtin" or (source == "project" and existing_source == "global"):
                pass  # project overrides global; builtin overridden by any saved tool
            else:
                return
        self._tools[spec.name] = spec
        if handler is not None:
            self._handlers[spec.name] = handler
        self._sources[spec.name] = source

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def list(self) -> List[ToolSpec]:
        return sorted(self._tools.values(), key=lambda s: s.name)

    def source_of(self, name: str) -> str:
        return self._sources.get(name, "?")

    # ── Persistence / self-extension ─────────────────────────────────────
    @property
    def _global_dir(self) -> Path:
        return GLOBAL_TOOLS_DIR

    @property
    def _project_dir(self) -> Path:
        return Path(self.project_root) / PROJECT_TOOLS_DIR

    def save_tool(self, spec: ToolSpec, scope: str = "project") -> Path:
        """Persist a custom tool definition. scope: 'project' | 'global'."""
        directory = self._project_dir if scope == "project" else self._global_dir
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{spec.name}.json"
        path.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
        self.register(spec, handler=None, source=scope)
        log.info("tools.saved", name=spec.name, scope=scope)
        return path

    def remove_tool(self, name: str, scope: Optional[str] = None) -> bool:
        removed = False
        candidates = [scope] if scope else ["project", "global"]
        for sc in candidates:
            directory = self._project_dir if sc == "project" else self._global_dir
            path = directory / f"{name}.json"
            if path.exists():
                path.unlink()
                removed = True
        self._tools.pop(name, None)
        self._handlers.pop(name, None)
        self._sources.pop(name, None)
        return removed

    def load_saved_tools(self) -> int:
        """Load custom tools from ~/.aztec/tools.d then project .aztec/tools."""
        count = 0
        for scope, directory in (("global", self._global_dir), ("project", self._project_dir)):
            if not directory.exists():
                continue
            for path in sorted(directory.glob("*.json")):
                try:
                    spec = ToolSpec.model_validate_json(path.read_text(encoding="utf-8"))
                    self.register(spec, handler=None, source=scope)
                    count += 1
                except Exception as exc:
                    log.warning("tools.load_failed", path=str(path), error=str(exc))
        return count

    # ── Execution ────────────────────────────────────────────────────────
    async def execute(self, name: str, raw_args: Dict[str, Any], ctx: ToolContext) -> ToolResult:
        spec = self._tools.get(name)
        if spec is None:
            return ToolResult(ok=False, error=f"unknown tool '{name}'")

        try:
            args = spec.coerce_args(raw_args)
        except ValueError as exc:
            return ToolResult(ok=False, error=f"invalid arguments: {exc}")

        allowed = await confirm_or_raise(ctx, name, spec.safety)
        if not allowed:
            return ToolResult(
                ok=False,
                error=f"execution of '{name}' ({spec.safety.value}) was not approved",
                exit_code=-1,
            )

        start = time.monotonic()
        try:
            handler = self._handlers.get(name)
            if handler is not None:
                result = await asyncio.wait_for(handler(args, ctx), timeout=spec.timeout_s)
            elif spec.template:
                result = await _run_shell(render_template(spec.template, args), ctx, spec.timeout_s, spec.output_cap_chars)
            else:
                result = ToolResult(ok=False, error=f"tool '{name}' has no handler or template")
        except asyncio.TimeoutError:
            result = ToolResult(ok=False, error=f"tool '{name}' timed out after {spec.timeout_s}s", exit_code=-1)
        except PermissionError as exc:
            result = ToolResult(ok=False, error=str(exc), exit_code=-1)
        except Exception as exc:  # noqa: BLE001 — tools must never crash the host
            result = ToolResult(ok=False, error=f"{type(exc).__name__}: {exc}", exit_code=-1)

        result.duration_ms = round((time.monotonic() - start) * 1000, 2)

        cap = spec.output_cap_chars
        if len(result.output) > cap:
            result.output = result.output[:cap]
            result.truncated = True

        self.audit(name, args, spec.safety, result)
        return result

    # ── Audit ────────────────────────────────────────────────────────────
    def audit(self, name: str, args: Dict[str, Any], safety: SafetyClass, result: ToolResult) -> None:
        try:
            audit_path = Path(self.project_root) / AUDIT_FILE
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            entry = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "tool": name,
                "safety": safety.value,
                "args": {k: (v if len(str(v)) < 200 else f"<{len(str(v))} chars>") for k, v in args.items()},
                "ok": result.ok,
                "exit_code": result.exit_code,
                "duration_ms": result.duration_ms,
            }
            with open(audit_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        except OSError as exc:
            log.warning("tools.audit_failed", error=str(exc))


# ── Shared shell runner for template tools ───────────────────────────────────

async def _run_shell(cmd: str, ctx: ToolContext, timeout_s: float, output_cap: int) -> ToolResult:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        cwd=str(ctx.root_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise TimeoutError(f"command exceeded {timeout_s}s")
    output = stdout.decode(errors="replace")[:output_cap * 2]
    return ToolResult(
        ok=(proc.returncode == 0),
        output=output,
        exit_code=proc.returncode or 0,
    )


_registry: Optional[Tuple[str, ToolRegistry]] = None


def get_registry(project_root: str = ".") -> ToolRegistry:
    """Per-project cached registry (rebuilt when the root changes)."""
    global _registry
    root = str(Path(project_root).expanduser().resolve())
    if _registry is None or _registry[0] != root:
        reg = ToolRegistry(project_root=root)
        register_builtins(reg)
        _registry = (root, reg)
    return _registry[1]


def register_builtins(registry: ToolRegistry) -> None:
    from aztec_circle.tools.builtins import BUILTIN_TOOLS
    for spec, handler in BUILTIN_TOOLS:
        registry.register(spec, handler, source="builtin")
