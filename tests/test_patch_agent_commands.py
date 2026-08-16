"""
Unit tests for PatchAgent command proposing, confirmation, and execution.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from rich.console import Console

from aztec_circle.adapters.llm_provider import LLMResponse
from aztec_circle.domain.models import ConsoleCommand, CommandExecutionResult
from aztec_circle.engine.patch_agent import PatchAgent, PatchResult
from aztec_circle.engine.plan_manager import PlanManager


@pytest.mark.asyncio
async def test_patch_agent_executes_confirmed_commands(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    app_file = src / "App.tsx"
    app_file.write_text("export const App = () => <div>App</div>;\n", encoding="utf-8")

    mock_provider = MagicMock()

    # Round 1 response
    r1_resp = LLMResponse(
        content=json.dumps({
            "reasoning": "Needs App.tsx",
            "files_to_read": ["src/App.tsx"]
        }),
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70,
        model="test-model",
    )

    # Round 2 response with patches and console commands
    r2_resp = LLMResponse(
        content=json.dumps({
            "edit_summary": "Added role management and ran DB migration",
            "patches": [
                {
                    "file": "src/App.tsx",
                    "action": "replace",
                    "start_line": 1,
                    "end_line": 1,
                    "replacement": "export const App = () => <div>App with Roles</div>;\n",
                    "concern": "Update UI",
                }
            ],
            "commands": [
                {
                    "command": "echo 'running pre-migration' > pre.txt",
                    "description": "Run pre-migration setup",
                    "stage": "pre_patch"
                },
                {
                    "command": "echo 'running post-migration' > post.txt",
                    "description": "Run post-migration setup",
                    "stage": "post_patch"
                }
            ]
        }),
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        model="test-model",
    )

    mock_provider.invoke = AsyncMock(side_effect=[r1_resp, r2_resp])

    agent = PatchAgent(provider=mock_provider, console=Console())

    # User confirms all commands
    confirm_cb = AsyncMock(return_value=(True, None))

    res = await agent.run(
        instruction="Add role management and migrate DB",
        project_dir=str(tmp_path),
        confirm_command_callback=confirm_cb,
    )

    assert res.success is True
    assert len(res.commands_proposed) == 2
    assert len(res.commands_executed) == 2
    assert all(c.success for c in res.commands_executed)
    assert all(c.confirmed for c in res.commands_executed)
    assert not any(c.skipped for c in res.commands_executed)

    assert (tmp_path / "pre.txt").exists()
    assert (tmp_path / "post.txt").exists()
    assert confirm_cb.call_count == 2


@pytest.mark.asyncio
async def test_patch_agent_skips_declined_command(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    app_file = src / "App.tsx"
    app_file.write_text("export const App = () => <div>App</div>;\n", encoding="utf-8")

    mock_provider = MagicMock()
    r1_resp = LLMResponse(
        content=json.dumps({"reasoning": "read app", "files_to_read": ["src/App.tsx"]}),
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70,
        model="test-model",
    )
    r2_resp = LLMResponse(
        content=json.dumps({
            "edit_summary": "Proposed destructive command",
            "patches": [],
            "commands": [
                {
                    "command": "touch should_not_exist.txt",
                    "description": "Create test file",
                    "stage": "post_patch"
                }
            ]
        }),
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        model="test-model",
    )
    mock_provider.invoke = AsyncMock(side_effect=[r1_resp, r2_resp])

    agent = PatchAgent(provider=mock_provider, console=Console())

    # User declines command
    confirm_cb = AsyncMock(return_value=(False, None))

    res = await agent.run(
        instruction="Try running touch",
        project_dir=str(tmp_path),
        confirm_command_callback=confirm_cb,
    )

    assert res.success is True
    assert len(res.commands_executed) == 1
    assert res.commands_executed[0].skipped is True
    assert not (tmp_path / "should_not_exist.txt").exists()


@pytest.mark.asyncio
async def test_patch_agent_custom_edited_command(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    app_file = src / "App.tsx"
    app_file.write_text("export const App = () => <div>App</div>;\n", encoding="utf-8")

    mock_provider = MagicMock()
    r1_resp = LLMResponse(
        content=json.dumps({"reasoning": "read app", "files_to_read": ["src/App.tsx"]}),
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70,
        model="test-model",
    )
    r2_resp = LLMResponse(
        content=json.dumps({
            "edit_summary": "Original command",
            "patches": [],
            "commands": [
                {
                    "command": "touch original.txt",
                    "description": "Original touch",
                    "stage": "post_patch"
                }
            ]
        }),
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        model="test-model",
    )
    mock_provider.invoke = AsyncMock(side_effect=[r1_resp, r2_resp])

    agent = PatchAgent(provider=mock_provider, console=Console())

    # User edits command to custom string
    confirm_cb = AsyncMock(return_value=(True, "touch edited.txt"))

    res = await agent.run(
        instruction="Touch file",
        project_dir=str(tmp_path),
        confirm_command_callback=confirm_cb,
    )

    assert res.success is True
    assert not (tmp_path / "original.txt").exists()
    assert (tmp_path / "edited.txt").exists()
    assert res.commands_executed[0].command == "touch edited.txt"


@pytest.mark.asyncio
async def test_patch_agent_auto_approve_commands(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    app_file = src / "App.tsx"
    app_file.write_text("export const App = () => <div>App</div>;\n", encoding="utf-8")

    mock_provider = MagicMock()
    r1_resp = LLMResponse(
        content=json.dumps({"reasoning": "read app", "files_to_read": ["src/App.tsx"]}),
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70,
        model="test-model",
    )
    r2_resp = LLMResponse(
        content=json.dumps({
            "edit_summary": "Auto approved command",
            "patches": [],
            "commands": [
                {
                    "command": "echo 'auto' > auto.txt",
                    "description": "Auto approved",
                    "stage": "post_patch"
                }
            ]
        }),
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        model="test-model",
    )
    mock_provider.invoke = AsyncMock(side_effect=[r1_resp, r2_resp])

    agent = PatchAgent(provider=mock_provider, console=Console())

    res = await agent.run(
        instruction="Auto run command",
        project_dir=str(tmp_path),
        auto_approve_commands=True,
    )

    assert res.success is True
    assert (tmp_path / "auto.txt").exists()
    assert res.commands_executed[0].success is True
