"""
Unit tests for Aztec Living Project Plan & Roadmap Manager (AZTEC_PLAN.md).
"""

import os
from pathlib import Path
from unittest.mock import MagicMock
import pytest
from rich.console import Console
from typer.testing import CliRunner

from aztec_circle.domain.models import CircleRunState, AgentRank, CirclePhase, PeerDraftOutput
from aztec_circle.engine.plan_manager import PlanManager, PLAN_FILENAME
from aztec_circle.tui.commands import dispatch_slash_command
from aztec_circle.tui.session import SessionState
from aztec_circle.cli import app

runner = CliRunner()


def test_plan_manager_generate_from_debate(tmp_path):
    """Verify PlanManager generates a rich AZTEC_PLAN.md following a debate."""
    state = CircleRunState(
        task_id="test-plan-1",
        goal="Build a Collaborative 3D Canvas",
        current_phase=CirclePhase.RESOLVED,
        peer_history=[
            PeerDraftOutput(
                architecture_overview="Atomic React three-fiber canvas architecture.",
                implementation_code={
                    "package.json": "{}",
                    "src/App.tsx": "export default function App() {}",
                    "src/components/Toolbar.tsx": "export function Toolbar() {}",
                    "src/engine/canvasMath.ts": "export function calc3D() {}",
                },
                mitigations_applied=[
                    "Separate 3D matrix math from React rendering loop.",
                ],
                assumptions_made=[
                    "WebGL2 supported.",
                ],
            )
        ],
        total_cost_usd=0.015,
    )

    plan_path = PlanManager.generate_or_update_from_debate(state, str(tmp_path))
    assert plan_path.exists()
    assert plan_path.name == PLAN_FILENAME

    content = plan_path.read_text(encoding="utf-8")
    assert "Build a Collaborative 3D Canvas" in content
    assert "Atomic React three-fiber canvas architecture." in content
    assert "src/App.tsx" in content
    assert "src/components/Toolbar.tsx" in content
    assert "src/engine/canvasMath.ts" in content
    assert "Separate 3D matrix math" in content
    assert "WebGL2 supported." in content


def test_plan_manager_record_edit_iteration(tmp_path):
    """Verify record_edit_iteration updates AZTEC_PLAN.md with edit history and new files."""
    # Create sample codebase
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "App.tsx").write_text("export default function App() {}")
    (tmp_path / "package.json").write_text("{}")

    PlanManager.sync_from_codebase(str(tmp_path), goal="My App")
    assert PlanManager.plan_exists(str(tmp_path))

    # Record an edit
    new_file = "src/components/ColorPicker.tsx"
    (tmp_path / "src" / "components").mkdir(parents=True, exist_ok=True)
    (tmp_path / new_file).write_text("export function ColorPicker() {}")

    PlanManager.record_edit_iteration(
        output_dir=str(tmp_path),
        instruction="Add color picker component",
        modified_files=["src/App.tsx", new_file],
    )

    content = PlanManager.read_plan(str(tmp_path))
    assert content is not None
    assert "Add color picker component" in content
    assert new_file in content
    assert "ColorPicker" in content


def test_plan_manager_record_fix_iteration(tmp_path):
    """Verify record_fix_iteration records self-healing compiler fixes."""
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "App.tsx").write_text("export default function App() {}")
    PlanManager.sync_from_codebase(str(tmp_path), goal="Fix App")

    PlanManager.record_fix_iteration(
        output_dir=str(tmp_path),
        fixed_files=["src/App.tsx"],
        error_summary="TS2304: Cannot find name 'React'",
    )

    content = PlanManager.read_plan(str(tmp_path))
    assert "Automated Self-Healing Build Fix" in content
    assert "TS2304" in content


def test_plan_manager_compact_plan_context(tmp_path):
    """Verify get_compact_plan_context generates a token-dense summary."""
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "App.tsx").write_text("export default function App() {}")
    PlanManager.sync_from_codebase(str(tmp_path), goal="Dense Test App")

    compact = PlanManager.get_compact_plan_context(str(tmp_path))
    assert "[PROJECT BLUEPRINT & ROADMAP CONTEXT]" in compact
    assert "Dense Test App" in compact
    assert "Atomic Directory Discipline" in compact
    assert len(compact) < 2000


def test_tui_slash_plan_commands(tmp_path):
    """Verify TUI /plan, /roadmap, and /plan sync commands."""
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "App.tsx").write_text("export default function App() {}")

    console = Console(record=True)
    state = SessionState()
    state.output_dir = str(tmp_path)
    state.last_goal = "TUI Plan Test"

    # Test /plan sync
    handled = pytest.mark.asyncio(dispatch_slash_command)
    import asyncio

    async def _run():
        h1 = await dispatch_slash_command("/plan sync", state, console)
        assert h1 is True

        h2 = await dispatch_slash_command("/plan", state, console)
        assert h2 is True

        h3 = await dispatch_slash_command("/roadmap", state, console)
        assert h3 is True

        h4 = await dispatch_slash_command("/plan file", state, console)
        assert h4 is True

    asyncio.run(_run())
    out = console.export_text()
    assert "Living Project Blueprint" in out
    assert "Implementation Roadmap" in out


def test_cli_plan_command(tmp_path):
    """Verify aztec plan CLI command."""
    (tmp_path / "src").mkdir(parents=True)
    (tmp_path / "src" / "App.tsx").write_text("export default function App() {}")

    # 1. Sync via CLI
    res = runner.invoke(app, ["plan", str(tmp_path), "--sync"])
    assert res.exit_code == 0
    assert "Living Blueprint" in res.stdout

    # 2. Show plan
    res_show = runner.invoke(app, ["plan", str(tmp_path)])
    assert res_show.exit_code == 0
    assert "Implementation Roadmap" in res_show.stdout

    # 3. File path only
    res_file = runner.invoke(app, ["plan", str(tmp_path), "--file"])
    assert res_file.exit_code == 0
    assert PLAN_FILENAME in res_file.stdout
