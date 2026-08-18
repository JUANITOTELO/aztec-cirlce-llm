"""
Unit tests for Phased Dependency Batching, AST Skeletons, and Multi-Stage Rollback in PatchAgent.
"""

import json
import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from rich.console import Console

from aztec_circle.adapters.llm_provider import LLMResponse
from aztec_circle.engine.patch_agent import BatchPlanner, EditStage, FilePatch, PatchAgent, PatchApplicator, PatchResult
from aztec_circle.engine.project_indexer import ProjectIndexer
from aztec_circle.engine.post_apply_verifier import PostApplyVerifier, VerificationResult


def test_batch_planner_clustering_small_file_set():
    files = ["src/App.tsx", "src/Header.tsx"]
    stages = BatchPlanner.cluster_files_into_stages(files, max_files_per_stage=4)
    assert len(stages) == 1
    assert stages[0].target_files == ["src/App.tsx", "src/Header.tsx"]


def test_batch_planner_clustering_multi_layer():
    files = [
        "src/types/user.ts",
        "src/types/auth.ts",
        "src/engine/authService.ts",
        "src/engine/sessionStore.ts",
        "src/components/LoginForm.tsx",
        "src/components/UserProfile.tsx",
        "src/tests/auth.test.ts",
    ]
    stages = BatchPlanner.cluster_files_into_stages(files, max_files_per_stage=3)
    assert len(stages) >= 3

    # First stage should contain types/contracts
    assert any("types" in f for f in stages[0].target_files)
    # Reference files should contain all other files
    for st in stages:
        for f in st.target_files:
            assert f not in st.reference_files


def test_batch_planner_explicit_phases():
    explicit_phases = [
        {"stage": 1, "name": "Contract Schema", "files": ["schema.sql", "types.ts"]},
        {"stage": 2, "name": "Backend Logic", "files": ["server.py"]},
        {"stage": 3, "name": "Frontend UI", "files": ["App.tsx", "Header.tsx"]},
    ]
    stages = BatchPlanner.cluster_files_into_stages(
        files=["schema.sql", "types.ts", "server.py", "App.tsx", "Header.tsx"],
        phases_payload=explicit_phases,
    )
    assert len(stages) == 3
    assert stages[0].name == "Contract Schema"
    assert stages[0].target_files == ["schema.sql", "types.ts"]
    assert stages[1].name == "Backend Logic"
    assert stages[1].target_files == ["server.py"]
    assert stages[2].name == "Frontend UI"
    assert stages[2].target_files == ["App.tsx", "Header.tsx"]


def test_project_indexer_extract_file_skeleton(tmp_path):
    ts_file = tmp_path / "service.ts"
    ts_content = """import { User } from './types';
import axios from 'axios';

export interface UserConfig {
  id: string;
  name: string;
  roles: string[];
}

export type AuthState = 'LOGGED_IN' | 'LOGGED_OUT';

export function authenticateUser(config: UserConfig): boolean {
  // 50 lines of complex authentication logic
  console.log("Authenticating...");
  const token = "secret";
  return true;
}

export class AuthService {
  private token: string = "";
  public login(): void {
    console.log("login");
  }
}
"""
    ts_file.write_text(ts_content, encoding="utf-8")
    skeleton = ProjectIndexer.extract_file_skeleton(str(ts_file), max_lines=20)
    assert "export interface UserConfig" in skeleton
    assert "export type AuthState" in skeleton
    assert "import { User }" in skeleton


def test_project_indexer_get_context_with_lod(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    target = src / "target.ts"
    target.write_text("const a = 1;\nconst b = 2;\n", encoding="utf-8")
    ref = src / "ref.ts"
    ref.write_text("export interface Ref { key: string; }\n", encoding="utf-8")

    indexer = ProjectIndexer()
    lod_ctx = indexer.get_context_with_lod(
        project_root=str(tmp_path),
        target_files=["src/target.ts"],
        reference_files=["src/ref.ts"],
    )
    assert "TARGET FILES FOR MODIFICATION" in lod_ctx
    assert "src/target.ts" in lod_ctx
    assert "REFERENCE / SIBLING CONTEXT" in lod_ctx
    assert "src/ref.ts" in lod_ctx


@pytest.mark.asyncio
async def test_patch_agent_multi_stage_execution(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    t_file = src / "types.ts"
    t_file.write_text("export type Mode = 'light';\n", encoding="utf-8")
    c_file = src / "Component.tsx"
    c_file.write_text("export const Comp = () => <div>light</div>;\n", encoding="utf-8")

    mock_provider = MagicMock()

    # Round 1: Returns explicit 2 phases
    r1_resp = LLMResponse(
        content=json.dumps({
            "reasoning": "Need types and component",
            "files_to_read": ["src/types.ts", "src/Component.tsx"],
            "phases": [
                {"stage": 1, "name": "Type Contracts", "files": ["src/types.ts"]},
                {"stage": 2, "name": "UI Components", "files": ["src/Component.tsx"]},
            ]
        }),
        prompt_tokens=100,
        completion_tokens=40,
        total_tokens=140,
        model="test-model",
    )

    # Stage 1 Patch
    r2_stage1 = LLMResponse(
        content=json.dumps({
            "edit_summary": "Updated Mode type",
            "patches": [
                {
                    "file": "src/types.ts",
                    "action": "replace",
                    "start_line": 1,
                    "end_line": 1,
                    "replacement": "export type Mode = 'light' | 'dark';",
                    "concern": "Add dark mode",
                }
            ]
        }),
        prompt_tokens=150,
        completion_tokens=50,
        total_tokens=200,
        model="test-model",
    )

    # Stage 2 Patch
    r2_stage2 = LLMResponse(
        content=json.dumps({
            "edit_summary": "Updated Comp JSX",
            "patches": [
                {
                    "file": "src/Component.tsx",
                    "action": "replace",
                    "start_line": 1,
                    "end_line": 1,
                    "replacement": "export const Comp = () => <div>dark</div>;",
                    "concern": "Update default JSX",
                }
            ]
        }),
        prompt_tokens=160,
        completion_tokens=50,
        total_tokens=210,
        model="test-model",
    )

    mock_provider.invoke = AsyncMock(side_effect=[r1_resp, r2_stage1, r2_stage2])

    agent = PatchAgent(provider=mock_provider, console=Console(record=True))
    result = await agent.run("Support dark mode across types and components", project_dir=str(tmp_path))

    assert result.success is True
    assert "src/types.ts" in result.files_touched
    assert "src/Component.tsx" in result.files_touched
    assert "'light' | 'dark'" in t_file.read_text(encoding="utf-8")
    assert "<div>dark</div>" in c_file.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_patch_agent_multi_stage_global_rollback(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    f1 = src / "f1.ts"
    f1.write_text("original f1\n", encoding="utf-8")
    f2 = src / "f2.ts"
    f2.write_text("original f2\n", encoding="utf-8")

    mock_provider = MagicMock()

    # Round 1 returns 2 phases
    r1_resp = LLMResponse(
        content=json.dumps({
            "files_to_read": ["src/f1.ts", "src/f2.ts"],
            "phases": [
                {"stage": 1, "name": "Stage 1", "files": ["src/f1.ts"]},
                {"stage": 2, "name": "Stage 2", "files": ["src/f2.ts"]},
            ]
        }),
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70,
        model="test-model",
    )

    # Stage 1 succeeds
    r2_stage1 = LLMResponse(
        content=json.dumps({
            "patches": [
                {
                    "file": "src/f1.ts",
                    "action": "replace",
                    "start_line": 1,
                    "end_line": 1,
                    "replacement": "modified f1\n",
                }
            ]
        }),
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70,
        model="test-model",
    )

    # Stage 2 raises exception during invocation
    mock_provider.invoke = AsyncMock(side_effect=[r1_resp, r2_stage1, RuntimeError("LLM connection crashed during stage 2")])

    agent = PatchAgent(provider=mock_provider, console=Console(record=True))
    result = await agent.run("Edit both files", project_dir=str(tmp_path))

    assert result.success is False
    # Global rollback must restore f1.ts to original content even though Stage 1 passed!
    assert f1.read_text(encoding="utf-8") == "original f1\n"
    assert f2.read_text(encoding="utf-8") == "original f2\n"
