"""
Tool subsystem core models: specs, results, execution context, safety classes.

Design principles (production bar):
- Every tool declares a SafetyClass; the registry enforces confirmation gates.
- Shell-template tools substitute arguments with shlex.quote — argument
  injection is structurally impossible.
- Filesystem tools are confined to the project root.
- All executions are audited to <project>/.aztec/tool_audit.jsonl.
"""

from __future__ import annotations

import shlex
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional
from pydantic import BaseModel, Field


class SafetyClass(str, Enum):
    READ_ONLY = "read_only"      # auto-run
    MUTATING = "mutating"        # confirm once unless session is auto-approved
    DANGEROUS = "dangerous"      # always confirm unless explicitly auto-approved


class ParamType(str, Enum):
    STR = "str"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"


class ParamSpec(BaseModel):
    name: str = Field(..., pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    type: ParamType = ParamType.STR
    required: bool = True
    default: Optional[str] = None
    description: str = ""
    pattern: Optional[str] = Field(
        None, description="Optional regex the raw string value must match before use"
    )


class ToolSpec(BaseModel):
    name: str = Field(..., pattern=r"^[a-z][a-z0-9_]{2,40}$")
    description: str
    safety: SafetyClass = SafetyClass.READ_ONLY
    params: Dict[str, ParamSpec] = Field(default_factory=dict)
    timeout_s: float = Field(60.0, ge=1.0, le=600.0)
    output_cap_chars: int = Field(10_000, ge=200, le=200_000)

    # Shell-template tools: handler generated from this command template.
    # Placeholders like {path} are replaced with shlex.quote(value).
    template: Optional[str] = None

    def coerce_args(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Validate + coerce raw args against the declared schema."""
        coerced: Dict[str, Any] = {}
        for name, pspec in self.params.items():
            value = raw.get(name, pspec.default)
            if value is None:
                if pspec.required:
                    raise ValueError(f"missing required argument '{name}'")
                continue
            coerced[name] = _coerce(name, value, pspec)
        unknown = set(raw) - set(self.params)
        if unknown:
            raise ValueError(f"unknown argument(s): {sorted(unknown)}")
        return coerced


def _coerce(name: str, value: Any, pspec: ParamSpec) -> Any:
    text = str(value)
    if pspec.pattern and not __import__("re").match(pspec.pattern, text):
        raise ValueError(f"argument '{name}' does not match required pattern {pspec.pattern!r}")
    try:
        if pspec.type == ParamType.INT:
            return int(text)
        if pspec.type == ParamType.FLOAT:
            return float(text)
        if pspec.type == ParamType.BOOL:
            return text.strip().lower() in ("1", "true", "yes", "on")
        return text
    except ValueError as exc:
        raise ValueError(f"argument '{name}' must be {pspec.type.value}") from exc


def render_template(template: str, args: Dict[str, Any]) -> str:
    """
    Substitute {placeholder} tokens with safely-quoted values so crafted
    argument strings can never break out into extra shell commands.
    """
    rendered = template
    for key, value in args.items():
        token = "{" + key + "}"
        if token in rendered:
            rendered = rendered.replace(token, shlex.quote(str(value)))
    return rendered


def params_from_template(template: str) -> Dict[str, "ParamSpec"]:
    """Derive string params from {placeholder} tokens (TUI convenience)."""
    import re

    tokens = re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", template or "")
    return {token: ParamSpec(name=token) for token in dict.fromkeys(tokens)}


@dataclass
class ToolResult:
    ok: bool
    output: str = ""
    error: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    truncated: bool = False


Handler = Callable[[Dict[str, Any], "ToolContext"], Awaitable[ToolResult]]


@dataclass
class ToolContext:
    project_root: str = "."
    auto_approve: bool = False
    confirm_cb: Optional[Callable[[str, SafetyClass], Awaitable[bool]]] = None
    env: Dict[str, str] = field(default_factory=dict)

    @property
    def root_path(self) -> Path:
        return Path(self.project_root).expanduser().resolve()

    def confine(self, target: str) -> Path:
        """Resolve `target` and refuse paths escaping the project root."""
        p = Path(target).expanduser()
        resolved = (p if p.is_absolute() else self.root_path / p).resolve()
        root = self.root_path
        if resolved != root and root not in resolved.parents:
            raise PermissionError(
                f"path escapes project root ({resolved} not under {root})"
            )
        return resolved


async def confirm_or_raise(ctx: ToolContext, tool_name: str, safety: SafetyClass) -> bool:
    """Enforce the confirmation gate for non-read-only tools."""
    if safety == SafetyClass.READ_ONLY or ctx.auto_approve:
        return True
    if ctx.confirm_cb is None:
        return False
    return bool(await ctx.confirm_cb(tool_name, safety))
