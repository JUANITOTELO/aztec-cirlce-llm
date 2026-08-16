"""
Unit tests for PatchAgent, PatchApplicator, and edit session routing.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from rich.console import Console

from aztec_circle.adapters.llm_provider import LLMResponse
from aztec_circle.engine.patch_agent import FilePatch, PatchAgent, PatchApplicator, PatchResult
from aztec_circle.tui.interactive import _is_edit_followup
from aztec_circle.tui.session import SessionState


def test_patch_applicator_replace_lines(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    toolbar = src / "Toolbar.tsx"
    toolbar.write_text("line 1\nline 2\nline 3\nline 4\nline 5\n", encoding="utf-8")

    patch = FilePatch(
        file="src/Toolbar.tsx",
        action="replace",
        start_line=2,
        end_line=4,
        replacement="replaced 2 to 4\nand another line\n",
        concern="Update middle section",
    )

    touched, created, deleted = PatchApplicator.apply(str(tmp_path), [patch])
    assert "src/Toolbar.tsx" in touched

    content = toolbar.read_text(encoding="utf-8")
    assert content == "line 1\nreplaced 2 to 4\nand another line\nline 5\n"


def test_patch_applicator_insert_before(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    app = src / "App.tsx"
    app.write_text("line 1\nline 2\n", encoding="utf-8")

    patch = FilePatch(
        file="src/App.tsx",
        action="insert_before",
        start_line=1,
        replacement="// Header Comment\n",
        concern="Add header",
    )

    PatchApplicator.apply(str(tmp_path), [patch])
    content = app.read_text(encoding="utf-8")
    assert content == "// Header Comment\nline 1\nline 2\n"


def test_patch_applicator_create_and_delete(tmp_path):
    # Test create
    create_patch = FilePatch(
        file="src/atoms/Button.tsx",
        action="create",
        replacement="export const Button = () => null;\n",
        concern="Create Button atom",
    )
    touched, created, deleted = PatchApplicator.apply(str(tmp_path), [create_patch])
    assert "src/atoms/Button.tsx" in created
    btn_file = tmp_path / "src" / "atoms" / "Button.tsx"
    assert btn_file.exists()
    assert "Button" in btn_file.read_text(encoding="utf-8")

    # Test delete
    del_patch = FilePatch(
        file="src/atoms/Button.tsx",
        action="delete",
        concern="Remove Button atom",
    )
    touched, created, deleted = PatchApplicator.apply(str(tmp_path), [del_patch])
    assert "src/atoms/Button.tsx" in deleted
    assert not btn_file.exists()


def test_patch_applicator_atomic_rollback_on_failure(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    target = src / "Existing.tsx"
    target.write_text("original content\n", encoding="utf-8")

    patch1 = FilePatch(
        file="src/Existing.tsx",
        action="replace",
        start_line=1,
        end_line=1,
        replacement="modified content\n",
    )

    # Patch 2 targets an invalid directory or raises on read
    class FaultyPatch:
        file = "src/Existing.tsx"
        action = "replace"
        start_line = 1
        end_line = 1
        @property
        def replacement(self):
            raise RuntimeError("Forced explosion during patch iteration")

    patch2 = FaultyPatch()

    with pytest.raises(RuntimeError):
        PatchApplicator.apply(str(tmp_path), [patch1, patch2])

    # Verify rollback restored the original content
    assert target.read_text(encoding="utf-8") == "original content\n"


@pytest.mark.asyncio
async def test_patch_agent_2_round_flow(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    toolbar = src / "Toolbar.tsx"
    toolbar.write_text("export const Toolbar = () => {\n  return <div>Old Toolbar</div>;\n};\n", encoding="utf-8")

    # Mock provider
    mock_provider = MagicMock()
    
    # Round 1 response
    r1_resp = LLMResponse(
        content=json.dumps({
            "reasoning": "Needs Toolbar.tsx",
            "files_to_read": ["src/Toolbar.tsx"]
        }),
        prompt_tokens=100,
        completion_tokens=30,
        total_tokens=130,
        model="test-model",
    )

    # Round 2 response
    r2_resp = LLMResponse(
        content=json.dumps({
            "edit_summary": "Updated toolbar JSX text",
            "patches": [
                {
                    "file": "src/Toolbar.tsx",
                    "action": "replace",
                    "start_line": 2,
                    "end_line": 2,
                    "replacement": "  return <div>Upgraded Modern Toolbar</div>;",
                    "concern": "Update toolbar title",
                }
            ]
        }),
        prompt_tokens=200,
        completion_tokens=80,
        total_tokens=280,
        model="test-model",
    )

    mock_provider.invoke = AsyncMock(side_effect=[r1_resp, r2_resp])

    agent = PatchAgent(provider=mock_provider, console=Console(record=True))
    result = await agent.run("Make the toolbar modern", project_dir=str(tmp_path), verbose=True)

    assert result.success is True
    assert result.edit_summary == "Updated toolbar JSX text"
    assert "src/Toolbar.tsx" in result.files_touched
    assert "Upgraded Modern Toolbar" in toolbar.read_text(encoding="utf-8")


def test_is_edit_followup_heuristics(tmp_path):
    state = SessionState()
    state.output_dir = str(tmp_path)
    state.edit_mode_enabled = True

    # No src directory yet -> False
    assert _is_edit_followup("Add a button", state) is False

    # Create src directory with a file
    src = tmp_path / "src"
    src.mkdir()
    (src / "App.tsx").write_text("export default function App() {}", encoding="utf-8")

    # Major project creation triggers -> False (full debate)
    assert _is_edit_followup("Create a 3D robot app", state) is False
    assert _is_edit_followup("Let's build an interactive audio visualizer", state) is False
    assert _is_edit_followup("Design a dashboard", state) is False

    # Follow-up incremental changes -> True (edit mode)
    assert _is_edit_followup("Add a screenshot capture button", state) is True
    assert _is_edit_followup("Change the background color to dark slate", state) is True
    assert _is_edit_followup("Fix the joint limits for elbow", state) is True
    assert _is_edit_followup("Extract Toolbar into its own atomic component", state) is True
