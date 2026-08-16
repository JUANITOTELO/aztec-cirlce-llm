"""
Unit tests for Vision-Enabled Multimodal Aztec Agents.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from rich.console import Console

from aztec_circle.adapters.llm_provider import LLMResponse
from aztec_circle.agents.youth import YouthAgent
from aztec_circle.agents.peer import PeerAgent
from aztec_circle.agents.elder import ElderAgent
from aztec_circle.domain.models import CircleRunState, FallbackPolicy, PeerDraftOutput, VerdictStatus
from aztec_circle.engine.patch_agent import PatchAgent
from aztec_circle.engine.state_machine import AztecOrchestrator
from aztec_circle.tui.commands import cmd_image, cmd_images, cmd_clear_images
from aztec_circle.tui.session import SessionState


@pytest.mark.asyncio
async def test_youth_agent_with_images():
    mock_provider = MagicMock()
    mock_provider.complete = AsyncMock(
        return_value=LLMResponse(
            content=json.dumps({
                "persona": "chaos_brainstormer",
                "identified_risks": [
                    {
                        "category": "Visual Contrast",
                        "description": "Mockup has insufficient contrast in toolbar badges",
                        "severity": "MEDIUM",
                        "suggested_mitigation": "Use high-contrast slate-900 border",
                        "is_showstopper": False,
                    }
                ],
                "override_triggered": False,
            }),
            prompt_tokens=150,
            completion_tokens=50,
            total_tokens=200,
            model="gemini-flash",
        )
    )

    agent = YouthAgent(persona="chaos_brainstormer", provider=mock_provider)
    result = await agent.run("Build from mockup", images=["data:image/png;base64,AAAA"])

    assert len(result.identified_risks) == 1
    assert result.identified_risks[0].category == "Visual Contrast"
    mock_provider.complete.assert_called_once()
    called_messages = mock_provider.complete.call_args[1]["messages"]
    user_msg_content = called_messages[1]["content"]
    assert isinstance(user_msg_content, list)
    assert user_msg_content[1]["type"] == "image_url"


@pytest.mark.asyncio
async def test_peer_agent_with_images():
    mock_provider = MagicMock()
    mock_provider.complete = AsyncMock(
        return_value=LLMResponse(
            content=json.dumps({
                "architecture_overview": "Decomposed UI from mockup into atomic components",
                "implementation_code": {
                    "package.json": "{}",
                    "src/App.tsx": "export default function App() {}",
                },
                "mitigations_applied": ["Applied dark palette matching screenshot"],
                "assumptions_made": [],
            }),
            prompt_tokens=300,
            completion_tokens=100,
            total_tokens=400,
            model="gemini-flash",
        )
    )

    agent = PeerAgent(provider=mock_provider)
    result = await agent.run("Build matching layout", youth_risks=[], images=["data:image/png;base64,BBBB"])

    assert "src/App.tsx" in result.implementation_code
    mock_provider.complete.assert_called_once()
    called_messages = mock_provider.complete.call_args[1]["messages"]
    user_msg_content = called_messages[1]["content"]
    assert isinstance(user_msg_content, list)
    assert user_msg_content[1]["type"] == "image_url"


@pytest.mark.asyncio
async def test_patch_agent_with_images(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "App.tsx").write_text("export default function App() { return <div>App</div>; }\n", encoding="utf-8")

    mock_provider = MagicMock()
    r1 = LLMResponse(
        content=json.dumps({"reasoning": "Edit App.tsx", "files_to_read": ["src/App.tsx"]}),
        prompt_tokens=100,
        completion_tokens=20,
        total_tokens=120,
        model="gemini-flash",
    )
    r2 = LLMResponse(
        content=json.dumps({
            "edit_summary": "Updated styling based on image",
            "patches": [
                {
                    "file": "src/App.tsx",
                    "action": "replace",
                    "start_line": 1,
                    "end_line": 1,
                    "replacement": "export default function App() { return <div className='bg-slate-900'>App</div>; }",
                    "concern": "Apply dark theme from image",
                }
            ]
        }),
        prompt_tokens=200,
        completion_tokens=50,
        total_tokens=250,
        model="gemini-flash",
    )
    mock_provider.invoke = AsyncMock(side_effect=[r1, r2])

    agent = PatchAgent(provider=mock_provider)
    result = await agent.run(
        "Match the colors in the attached mockup",
        project_dir=str(tmp_path),
        images=["data:image/png;base64,CCCC"],
    )

    assert result.success is True
    assert "src/App.tsx" in result.files_touched
    assert "bg-slate-900" in (src / "App.tsx").read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_tui_image_slash_commands(tmp_path):
    state = SessionState()
    console = Console(record=True)

    img = tmp_path / "mockup.png"
    img.write_bytes(b"dummy")

    # 1. Attach image
    await cmd_image(str(img), state, console)
    assert len(state.attached_images) == 1
    assert "📷 1" in state.prompt_text()

    # 2. List images
    await cmd_images("", state, console)
    output = console.export_text()
    assert "Attached Reference Images" in output

    # 3. Clear images
    await cmd_clear_images("", state, console)
    assert len(state.attached_images) == 0
    assert "📷" not in state.prompt_text()
