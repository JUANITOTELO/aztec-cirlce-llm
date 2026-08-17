"""
Unit tests for Aztec Modular Edit Consensus Engine.
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from rich.console import Console

from aztec_circle.adapters.llm_provider import LLMResponse
from aztec_circle.domain.models import (
    ElderAuditItem,
    ElderVerdict,
    ModularDraftOutput,
    ModularPatchItem,
    VerdictStatus,
    YouthBrainstormOutput,
)
from aztec_circle.engine.modular_consensus import (
    ModularConsensusOrchestrator,
    ModularConsensusResult,
)
from aztec_circle.engine.plan_manager import PlanManager


@pytest.mark.asyncio
async def test_modular_consensus_orchestrator_success(tmp_path):
    # Setup initial project structure
    src = tmp_path / "src"
    src.mkdir()
    types_dir = src / "types"
    types_dir.mkdir()
    store_file = types_dir / "store.ts"
    store_file.write_text("export interface RootState {\n  user: string;\n}\n", encoding="utf-8")

    app_file = src / "App.tsx"
    app_file.write_text("export const App = () => <div>App</div>;\n", encoding="utf-8")

    mock_provider = MagicMock()

    # Youth Chaos response
    youth1_resp = LLMResponse(
        content=json.dumps({
            "radical_ideas": ["Add real-time inventory alerts"],
            "identified_risks": [
                {
                    "category": "StateManagement",
                    "description": "Product state must not conflict with user state",
                    "severity": "MEDIUM",
                    "suggested_mitigation": "Isolate in useProductsStore hook",
                    "is_showstopper": False
                }
            ],
            "override_triggered": False
        }),
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70,
        model="test-model",
    )

    # Youth Advocate response
    youth2_resp = LLMResponse(
        content=json.dumps({
            "radical_ideas": [],
            "identified_risks": [],
            "override_triggered": False
        }),
        prompt_tokens=50,
        completion_tokens=20,
        total_tokens=70,
        model="test-model",
    )

    # Peer Modular Drafter response (includes patches for mandatory coordinator App.tsx and store.ts)
    peer_resp = LLMResponse(
        content=json.dumps({
            "architecture_overview": "Products module with isolated state and UI manager",
            "new_files": {
                "src/components/Products/ProductManager.tsx": "export const ProductManager = () => <div>Products</div>;\n",
                "src/hooks/useProducts.ts": "export const useProducts = () => ({ products: [] });\n"
            },
            "patches": [
                {
                    "file": "src/types/store.ts",
                    "action": "replace",
                    "start_line": 2,
                    "end_line": 2,
                    "replacement": "  user: string;\n  productsModuleEnabled: boolean;\n",
                    "concern": "Add products flag to RootState"
                },
                {
                    "file": "src/App.tsx",
                    "action": "replace",
                    "start_line": 1,
                    "end_line": 1,
                    "replacement": "import { ProductManager } from './components/Products/ProductManager';\nexport const App = () => <div><ProductManager /></div>;\n",
                    "concern": "Wire ProductManager into root coordinator"
                }
            ],
            "commands": [
                {
                    "command": "echo 'migrated' > db_status.txt",
                    "description": "Initialize products table",
                    "stage": "post_patch"
                }
            ],
            "mitigations_applied": ["Isolated state in useProducts hook"],
            "assumptions_made": ["Vite React TS ecosystem"]
        }),
        prompt_tokens=100,
        completion_tokens=50,
        total_tokens=150,
        model="test-model",
    )

    # Elder Security Auditor response
    elder1_resp = LLMResponse(
        content=json.dumps({
            "status": "APPROVED",
            "weighted_score": 9.2,
            "audit_items": [
                {"criterion": "Security & Access Governance", "weight": 0.5, "score": 9.2, "passed": True}
            ],
            "critical_flaws": []
        }),
        prompt_tokens=80,
        completion_tokens=30,
        total_tokens=110,
        model="test-model",
    )

    # Elder Structural Auditor response
    elder2_resp = LLMResponse(
        content=json.dumps({
            "status": "APPROVED",
            "weighted_score": 9.0,
            "audit_items": [
                {"criterion": "Integration & Non-Breaking Modularity", "weight": 0.5, "score": 9.0, "passed": True}
            ],
            "critical_flaws": []
        }),
        prompt_tokens=80,
        completion_tokens=30,
        total_tokens=110,
        model="test-model",
    )

    mock_provider.invoke = AsyncMock(side_effect=[
        youth1_resp, youth2_resp, peer_resp, elder1_resp, elder2_resp
    ])

    orchestrator = ModularConsensusOrchestrator(
        project_dir=str(tmp_path),
        goal="Create a product management module",
        provider=mock_provider,
        console=Console(),
    )

    # User confirms command
    confirm_cb = AsyncMock(return_value=(True, None))

    res = await orchestrator.run(
        confirm_command_callback=confirm_cb,
        verbose=False,
    )

    assert res.success is True
    assert len(res.new_files) == 2
    assert "src/components/Products/ProductManager.tsx" in res.new_files
    assert "src/hooks/useProducts.ts" in res.new_files
    assert (tmp_path / "src" / "components" / "Products" / "ProductManager.tsx").exists()
    assert (tmp_path / "src" / "hooks" / "useProducts.ts").exists()

    # Verify patches were applied
    store_content = store_file.read_text(encoding="utf-8")
    assert "productsModuleEnabled" in store_content
    app_content = app_file.read_text(encoding="utf-8")
    assert "ProductManager" in app_content

    # Verify command was executed
    assert (tmp_path / "db_status.txt").exists()

    # Verify plan was updated
    plan_path = PlanManager.get_plan_path(str(tmp_path))
    assert plan_path.exists()
    plan_text = plan_path.read_text(encoding="utf-8")
    assert "Module Consensus: Create a product management module" in plan_text


@pytest.mark.asyncio
async def test_modular_consensus_elder_rework_loop(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    app_file = src / "App.tsx"
    app_file.write_text("export const App = () => <div>App</div>;\n", encoding="utf-8")

    mock_provider = MagicMock()

    # Youth
    youth1 = LLMResponse(content=json.dumps({"identified_risks": []}), prompt_tokens=20, completion_tokens=10, total_tokens=30, model="t")
    youth2 = LLMResponse(content=json.dumps({"identified_risks": []}), prompt_tokens=20, completion_tokens=10, total_tokens=30, model="t")

    # Loop 0: Peer draft 1 (missing App.tsx wiring and skeleton)
    peer_draft1 = LLMResponse(
        content=json.dumps({
            "architecture_overview": "Initial incomplete draft",
            "new_files": {"src/components/Module.tsx": "export const Mod = () => null;\n"},
            "patches": []
        }),
        prompt_tokens=50, completion_tokens=20, total_tokens=70, model="t"
    )

    # Loop 0: Elder 1 rejects
    elder1_reject = LLMResponse(
        content=json.dumps({
            "status": "REJECTED",
            "weighted_score": 5.0,
            "critical_flaws": ["Component is skeleton placeholder"],
            "reworking_instructions": "Implement full interactive module"
        }),
        prompt_tokens=50, completion_tokens=20, total_tokens=70, model="t"
    )
    # Loop 0: Elder 2 rejects
    elder2_reject = LLMResponse(
        content=json.dumps({
            "status": "REJECTED",
            "weighted_score": 6.0,
            "critical_flaws": ["Missing state hook"],
            "reworking_instructions": "Add state hook"
        }),
        prompt_tokens=50, completion_tokens=20, total_tokens=70, model="t"
    )

    # Loop 1: Peer draft 2 (reworked with full module + App.tsx coordinator patch)
    peer_draft2 = LLMResponse(
        content=json.dumps({
            "architecture_overview": "Complete reworked module",
            "new_files": {"src/components/Module.tsx": "export const Mod = () => <div>Full Module</div>;\n"},
            "patches": [
                {
                    "file": "src/App.tsx",
                    "action": "replace",
                    "start_line": 1,
                    "end_line": 1,
                    "replacement": "export const App = () => <div><Mod /></div>;\n",
                    "concern": "Wire Mod into App"
                }
            ]
        }),
        prompt_tokens=60, completion_tokens=30, total_tokens=90, model="t"
    )

    # Loop 1: Elders approve
    elder1_approve = LLMResponse(
        content=json.dumps({"status": "APPROVED", "weighted_score": 9.5, "critical_flaws": []}),
        prompt_tokens=50, completion_tokens=20, total_tokens=70, model="t"
    )
    elder2_approve = LLMResponse(
        content=json.dumps({"status": "APPROVED", "weighted_score": 9.0, "critical_flaws": []}),
        prompt_tokens=50, completion_tokens=20, total_tokens=70, model="t"
    )

    mock_provider.invoke = AsyncMock(side_effect=[
        youth1, youth2,
        peer_draft1, elder1_reject, elder2_reject,
        peer_draft2, elder1_approve, elder2_approve,
    ])

    orchestrator = ModularConsensusOrchestrator(
        project_dir=str(tmp_path),
        goal="Add module with rework",
        provider=mock_provider,
        console=Console(),
        max_loops=2,
    )

    res = await orchestrator.run(verbose=False)
    assert res.success is True
    assert res.loop_count == 1
    assert (tmp_path / "src" / "components" / "Module.tsx").read_text(encoding="utf-8") == "export const Mod = () => <div>Full Module</div>;\n"


@pytest.mark.asyncio
async def test_modular_consensus_skips_invalid_new_file_keys(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    app_file = src / "App.tsx"
    app_file.write_text("export const App = () => <div>App</div>;\n", encoding="utf-8")

    mock_provider = MagicMock()

    youth1 = LLMResponse(content=json.dumps({"identified_risks": []}), prompt_tokens=20, completion_tokens=10, total_tokens=30, model="t")
    youth2 = LLMResponse(content=json.dumps({"identified_risks": []}), prompt_tokens=20, completion_tokens=10, total_tokens=30, model="t")

    # Peer draft with garbage keys mixed with valid keys and App.tsx patch
    peer_draft = LLMResponse(
        content=json.dumps({
            "architecture_overview": "Draft with mixed keys",
            "new_files": {
                "category": "invalid content",
                "color": "invalid content",
                "payload": "invalid content",
                "src/types/category.ts": "export interface Category { id: string; }\n",
            },
            "patches": [
                {
                    "file": "src/App.tsx",
                    "action": "replace",
                    "start_line": 1,
                    "end_line": 1,
                    "replacement": "export const App = () => <div>Categories App</div>;\n",
                    "concern": "Wire categories"
                }
            ]
        }),
        prompt_tokens=50, completion_tokens=20, total_tokens=70, model="t"
    )

    elder1 = LLMResponse(
        content=json.dumps({"status": "APPROVED", "weighted_score": 9.0, "critical_flaws": []}),
        prompt_tokens=50, completion_tokens=20, total_tokens=70, model="t"
    )
    elder2 = LLMResponse(
        content=json.dumps({"status": "APPROVED", "weighted_score": 9.0, "critical_flaws": []}),
        prompt_tokens=50, completion_tokens=20, total_tokens=70, model="t"
    )

    mock_provider.invoke = AsyncMock(side_effect=[youth1, youth2, peer_draft, elder1, elder2])

    orchestrator = ModularConsensusOrchestrator(
        project_dir=str(tmp_path),
        goal="Add categories",
        provider=mock_provider,
        console=Console(),
    )

    res = await orchestrator.run(verbose=False)
    assert res.success is True
    # Only valid file path should be created
    assert res.new_files == ["src/types/category.ts"]
    assert (tmp_path / "src" / "types" / "category.ts").exists()
    # Garbage files must NOT exist
    assert not (tmp_path / "category").exists()
    assert not (tmp_path / "color").exists()
    assert not (tmp_path / "payload").exists()
