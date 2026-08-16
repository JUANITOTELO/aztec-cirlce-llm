"""
Tests for Aztec BuildFixAgent and self-healing build error loop.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from rich.console import Console

from aztec_circle.adapters.llm_provider import LLMResponse
from aztec_circle.engine.build_fixer import BuildFixAgent, TSError, FixResult
from aztec_circle.engine.project_runner import CommandResult, ProjectRunner
from aztec_circle.engine.scaffolder import detect_uses_tailwind, detect_heavy_deps, scaffold_project
from aztec_circle.cli import slugify_goal


def test_slugify_goal():
    goal1 = "Let's create a modern production ready React TS app that renders Dummy 13"
    slug1 = slugify_goal(goal1)
    assert "dummy" in slug1 or "modern" in slug1 or "production" in slug1
    assert " " not in slug1

    goal2 = "Build an audio visualizer"
    slug2 = slugify_goal(goal2)
    assert slug2 == "audio_visualizer"


def test_parse_ts_errors():
    agent = BuildFixAgent()
    sample_error = """
src/components/3d/Dummy13Model.tsx(1,26): error TS6133: 'useRef' is declared but its value is never read.
src/utils/constants.ts(173,28): error TS2304: Cannot find name 'EulerRotation'.
"""
    errors = agent.parse_errors(sample_error)
    assert len(errors) == 2
    assert errors[0].file == "src/components/3d/Dummy13Model.tsx"
    assert errors[0].line == 1
    assert errors[0].code == "TS6133"
    assert "'useRef' is declared" in errors[0].message
    assert errors[1].file == "src/utils/constants.ts"
    assert errors[1].line == 173
    assert errors[1].code == "TS2304"


def test_detect_uses_tailwind_css(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "index.css").write_text("@tailwind base;\n@tailwind components;\n@tailwind utilities;\n", encoding="utf-8")
    assert detect_uses_tailwind(str(tmp_path)) is True


def test_detect_uses_tailwind_package_json(tmp_path):
    pkg = {"devDependencies": {"tailwindcss": "^3.4.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    assert detect_uses_tailwind(str(tmp_path)) is True


def test_detect_heavy_deps_three(tmp_path):
    pkg = {"dependencies": {"three": "^0.164.0", "@react-three/fiber": "^8.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    heavy = detect_heavy_deps(str(tmp_path))
    assert "three" in heavy
    assert "@react-three/fiber" in heavy


def test_scaffold_project_injects_tailwind_and_chunks(tmp_path):
    pkg = {
        "name": "three-app",
        "dependencies": {"react": "^18.0.0", "three": "^0.164.0"},
        "devDependencies": {"tailwindcss": "^3.4.0"}
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg), encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "App.tsx").write_text("export default function App() {}", encoding="utf-8")

    res = scaffold_project(str(tmp_path))
    assert "tailwind.config.js" in res.files_injected
    assert "postcss.config.js" in res.files_injected
    assert "vite.config.ts" in res.files_injected

    # Verify injected vite.config.ts has chunking
    vite_cfg = (tmp_path / "vite.config.ts").read_text(encoding="utf-8")
    assert "manualChunks" in vite_cfg
    assert "vendor-three" in vite_cfg


@pytest.mark.asyncio
async def test_build_fix_agent_successful_healing(tmp_path):
    # Setup a project file with a simulated error
    src = tmp_path / "src"
    src.mkdir()
    broken_file = src / "constants.ts"
    broken_file.write_text("export const ZERO_POSE: MannequinPose = {};", encoding="utf-8")

    initial_fail = CommandResult(
        success=False,
        stdout="",
        stderr="src/constants.ts(1,25): error TS2304: Cannot find name 'MannequinPose'.",
        exit_code=2,
        duration_seconds=0.5,
    )

    mock_llm_response = LLMResponse(
        content=json.dumps({
            "fixes_summary": "Imported MannequinPose interface",
            "patched_files": {
                "src/constants.ts": "export interface MannequinPose {};\nexport const ZERO_POSE: MannequinPose = {};"
            }
        }),
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        model="test-model",
    )

    mock_provider = MagicMock()
    mock_provider.invoke = AsyncMock(return_value=mock_llm_response)

    runner = ProjectRunner(console=Console(record=True))
    success_build = CommandResult(success=True, stdout="built", stderr="", exit_code=0, duration_seconds=0.2)

    with patch.object(runner, "build_project", new_callable=AsyncMock, return_value=success_build):
        fixer = BuildFixAgent(provider=mock_provider, console=Console(record=True), max_iterations=2)
        fix_res = await fixer.fix(str(tmp_path), initial_fail, runner=runner)

        assert fix_res.success is True
        assert fix_res.iterations == 1
        assert "src/constants.ts" in fix_res.patches_applied
        # Verify file on disk was patched
        assert "export interface MannequinPose" in broken_file.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_build_fix_agent_already_clean():
    clean_build = CommandResult(success=True, stdout="built", stderr="", exit_code=0, duration_seconds=0.2)
    fixer = BuildFixAgent()
    res = await fixer.fix("/tmp", clean_build)
    assert res.success is True
    assert res.iterations == 0
