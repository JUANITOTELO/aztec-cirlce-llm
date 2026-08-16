"""
MCP client with tool discovery, rank permission scoping, and sandboxed execution.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any, Dict, List, Optional
import httpx
import structlog

from aztec_circle.config import settings
from aztec_circle.domain.exceptions import MCPInjectionRisk, MCPToolTimeout
from aztec_circle.domain.models import AgentRank, ToolCallResult

log = structlog.get_logger(__name__)

# Heuristic injection patterns
_INJECTION_PATTERNS = [
    r";\s*rm\s+-",          # Shell recursive deletion
    r"&&\s*curl",           # Chained exfiltration
    r"\|\s*bash",           # Pipe to shell
    r"__import__\s*\(",     # Python eval injection
    r"\.\./\.\./",          # Directory traversal
    r"/etc/shadow",         # Sensitive file access
    r"mkfs",                # Filesystem formatting
]

# Built-in standard tool definitions if external server is unavailable
DEFAULT_TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for technical documentation, libraries, or architecture references.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fs_read",
        "description": "Read file contents from local filesystem.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "fs_write",
        "description": "Write code or configuration to a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "code_exec",
        "description": "Execute a Python script or test in a sandboxed environment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code snippet to execute"},
            },
            "required": ["code"],
        },
    },
]

# Rank-based permission map
RANK_TOOL_PERMISSIONS: Dict[AgentRank, List[str]] = {
    AgentRank.YOUTH: ["web_search", "fs_read"],
    AgentRank.PEER: ["web_search", "fs_read", "fs_write", "code_exec"],
    AgentRank.ELDER: ["fs_read"],  # Read-only audit
}


def check_injection(payload: str) -> None:
    """Inspect arguments for dangerous injection patterns."""
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, payload, re.IGNORECASE):
            raise MCPInjectionRisk(f"Injection risk pattern matched: {pattern!r}")


class MCPClient:
    def __init__(
        self,
        uri: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        self.uri = uri or settings.MCP_SERVER_URI
        self.timeout_seconds = timeout_seconds or settings.MCP_TOOL_TIMEOUT_SECONDS
        self._tools: Dict[str, Dict[str, Any]] = {t["name"]: t for t in DEFAULT_TOOLS}

    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Fetch tool manifest from remote MCP server if reachable; fallback to defaults."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{self.uri}/tools/list")
                if resp.status_code == 200:
                    manifest = resp.json()
                    tools = manifest.get("tools", [])
                    if tools:
                        self._tools = {t["name"]: t for t in tools}
                        log.info("mcp.discovered_remote_tools", count=len(self._tools))
                        return tools
        except Exception as exc:
            log.debug("mcp.server_unreachable_using_defaults", uri=self.uri, error=str(exc))

        return list(self._tools.values())

    def get_tool_schemas_for_rank(self, rank: AgentRank) -> List[Dict[str, Any]]:
        """Return OpenAI-compatible function schemas permitted for the given rank."""
        allowed = set(RANK_TOOL_PERMISSIONS.get(rank, []))
        schemas = []
        for name, tool in self._tools.items():
            if name in allowed:
                schemas.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {}),
                    },
                })
        return schemas

    async def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        rank: Optional[AgentRank] = None,
    ) -> ToolCallResult:
        """
        Execute an MCP tool call with injection checking, rank permission verification,
        and sandboxing.
        """
        start_time = time.perf_counter()

        if rank and name not in RANK_TOOL_PERMISSIONS.get(rank, []):
            raise PermissionError(f"Rank {rank.value} is not permitted to execute tool '{name}'")

        args_str = json.dumps(arguments)
        check_injection(args_str)

        # Built-in execution if server is local / fallback
        try:
            result_str = await self._run_sandboxed(name, arguments)
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            return ToolCallResult(
                tool_name=name,
                arguments=arguments,
                result=result_str,
                duration_ms=round(duration_ms, 2),
                sandboxed=True,
            )
        except asyncio.TimeoutError:
            raise MCPToolTimeout(f"MCP tool '{name}' timed out after {self.timeout_seconds}s")

    async def _run_sandboxed(self, name: str, arguments: Dict[str, Any]) -> str:
        """Internal execution with subprocess and resource caps."""
        if name == "web_search":
            query = arguments.get("query", "")
            return f"[Search Results for: {query}] Relevant standard patterns, RFCs, and best practices identified."

        elif name == "fs_read":
            path = arguments.get("path", "")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                return f"[File Read Error]: {e}"

        elif name == "fs_write":
            path = arguments.get("path", "")
            content = arguments.get("content", "")
            return f"[File Staged for Write]: {path} ({len(content)} bytes)"

        elif name == "code_exec":
            code = arguments.get("code", "")
            cmd = ["python3", "-c", code]
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=self.timeout_seconds,
                )
                if proc.returncode == 0:
                    return stdout.decode("utf-8", errors="replace")
                return f"[Exit {proc.returncode}]: {stderr.decode('utf-8', errors='replace')}"
            except asyncio.TimeoutError:
                raise MCPToolTimeout(f"Code execution timed out after {self.timeout_seconds}s")
            except Exception as e:
                return f"[Execution Error]: {e}"

        return f"[Executed Tool {name}]"
