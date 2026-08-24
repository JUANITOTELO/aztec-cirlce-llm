"""
Bridge between debate agents and the ToolRegistry.

Implements a bounded tool-use loop: the model may respond to its drafting
prompt with {"tool_requests": [{"tool": ..., "args": {...}}]} instead of a
final answer; read-only tools execute automatically (mutating/dangerous go
through the confirmation gate and are simply denied when no approver is
wired); results are appended to the conversation and the model gets one more
chance to produce its full structured output.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
import structlog

from aztec_circle.agents.base import extract_json_payload
from aztec_circle.tools import SafetyClass, ToolContext, ToolRegistry

log = structlog.get_logger(__name__)

MAX_TOOL_ROUNDS = 2

TOOL_PROTOCOL_INSTRUCTIONS = """\
PROJECT TOOL ACCESS:
You are connected to a live sandboxed tool registry for this machine. Before
finalizing, you MAY inspect the real project by replying with ONLY:

{"tool_requests": [{"tool": "<name>", "args": {...}, "reason": "<why>"}]}

Rules:
- read_only tools run automatically; mutating/dangerous tools require operator
  approval and will be denied silently otherwise.
- Up to {max_rounds} tool rounds are available. After TOOL RESULTS are returned,
  you MUST immediately produce your FULL final JSON deliverable (no further
  tool_requests).
Available tools:
{menu}
"""


def build_tool_menu(registry: ToolRegistry) -> str:
    lines: List[str] = []
    for spec in registry.list():
        params = ", ".join(
            f"{name}:{pspec.type.value}{'' if pspec.required else ' (opt)'}"
            for name, pspec in spec.params.items()
        ) or "—"
        lines.append(f"- {spec.name} [{spec.safety.value}] ({params}): {spec.description[:90]}")
    return "\n".join(lines)


def build_tool_prompt(registry: ToolRegistry, max_rounds: int = MAX_TOOL_ROUNDS) -> str:
    # .replace() rather than .format(): the protocol embeds literal JSON braces.
    return (
        TOOL_PROTOCOL_INSTRUCTIONS
        .replace("{max_rounds}", str(max_rounds))
        .replace("{menu}", build_tool_menu(registry))
    )


def parse_tool_requests(content: str) -> List[Dict[str, Any]]:
    """
    Extract tool_requests from a model response. Returns [] unless the payload
    explicitly contains a non-empty tool_requests array (so ordinary drafts
    never trigger the loop).
    """
    if "tool_requests" not in (content or ""):
        return []
    data = extract_json_payload(content)
    requests = data.get("tool_requests")
    if not isinstance(requests, list):
        return []
    cleaned: List[Dict[str, Any]] = []
    for req in requests[:8]:  # hard cap per round
        if isinstance(req, dict) and req.get("tool"):
            cleaned.append({"tool": str(req["tool"]), "args": req.get("args") or {}, "reason": req.get("reason")})
    return cleaned


async def execute_tool_requests(
    requests: List[Dict[str, Any]],
    registry: ToolRegistry,
    ctx: ToolContext,
) -> List[Dict[str, Any]]:
    """
    Execute tool requests sequentially; every outcome (including denials and
    errors) becomes a result record so the model can adapt.
    """
    results: List[Dict[str, Any]] = []
    for req in requests:
        name = req.get("tool", "")
        spec = registry.get(name)
        if spec is None:
            results.append({"tool": name, "ok": False, "error": f"unknown tool '{name}'"})
            continue
        if spec.safety != SafetyClass.READ_ONLY and ctx.confirm_cb is None and not ctx.auto_approve:
            results.append({
                "tool": name,
                "ok": False,
                "denied": True,
                "error": f"'{name}' is {spec.safety.value} and requires operator approval; continue without it",
            })
            log.info("agent_tools.denied", tool=name, safety=spec.safety.value)
            continue
        res = await registry.execute(name, req.get("args") or {}, ctx)
        record: Dict[str, Any] = {
            "tool": name,
            "ok": res.ok,
            "exit_code": res.exit_code,
        }
        if res.output:
            record["output"] = res.output[:4000]
        if res.error:
            record["error"] = res.error
        results.append(record)
    return results


def render_tool_results(results: List[Dict[str, Any]]) -> str:
    body = "\n".join(f"- {json.dumps(r)[:1500]}" for r in results) or "(no results)"
    return (
        "TOOL RESULTS:\n"
        f"{body}\n\n"
        "You have used your tool budget. Produce your FULL final JSON deliverable now."
    )
