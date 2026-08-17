"""
Unit tests for Aztec LinkingEngine, IntegrationPatchEnforcer, and PostApplyVerifier.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

from aztec_circle.domain.models import ModularPatchItem
from aztec_circle.engine.integration_enforcer import enforce_mandatory_patches
from aztec_circle.engine.linking_engine import (
    DependencyGraph,
    FileNode,
    IntegrationManifest,
    LinkingEngine,
    load_project_aztec_config,
)
from aztec_circle.engine.post_apply_verifier import PostApplyVerifier, VerificationResult


def test_linking_engine_ts_graph_and_entry_points():
    """Verify dependency graph construction and entry point heuristic detection in TypeScript."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mockup files
        src_dir = Path(tmpdir) / "src"
        src_dir.mkdir(parents=True)
        components_dir = src_dir / "components"
        components_dir.mkdir()

        app_tsx = src_dir / "App.tsx"
        app_tsx.write_text(
            """
import React from 'react';
import { ProductList } from './components/ProductList';
import { db } from './db/dexie';

export function App() {
  return <div>App</div>;
}
export default App;
""",
            encoding="utf-8",
        )

        db_dir = src_dir / "db"
        db_dir.mkdir()
        dexie_ts = db_dir / "dexie.ts"
        dexie_ts.write_text(
            """
import Dexie from 'dexie';
export class AppDB extends Dexie {}
export const db = new AppDB();
""",
            encoding="utf-8",
        )

        prod_list = components_dir / "ProductList.tsx"
        prod_list.write_text(
            """
import React from 'react';
import { db } from '../db/dexie';
export const ProductList = () => <div />;
""",
            encoding="utf-8",
        )

        engine = LinkingEngine()
        graph = engine.build_graph(tmpdir)

        assert "src/App.tsx" in graph.nodes
        assert "src/db/dexie.ts" in graph.nodes
        assert "src/components/ProductList.tsx" in graph.nodes

        # Verify entry point auto-detection
        assert graph.entry_points.get("src/App.tsx") == "react_root"
        assert graph.entry_points.get("src/db/dexie.ts") == "indexed_db"

        # Verify reverse edges: dexie.ts should be imported by App.tsx and ProductList.tsx
        dexie_node = graph.nodes["src/db/dexie.ts"]
        assert "src/App.tsx" in dexie_node.imported_by
        assert "src/components/ProductList.tsx" in dexie_node.imported_by

        # Verify integration manifest
        manifest = engine.build_integration_manifest(graph, goal="Add product variations")
        assert "src/App.tsx" in manifest.mandatory_patch_targets
        assert "src/db/dexie.ts" in manifest.mandatory_patch_targets
        assert "src/db/dexie.ts" in manifest.hotspot_files

        context_str = engine.to_prompt_context(manifest)
        assert "DEPENDENCY GRAPH" in context_str
        assert "MANDATORY INTEGRATION TARGETS" in context_str


def test_linking_engine_config_overrides():
    """Verify that .aztec.json config overrides and extra_key_files take precedence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        aztec_json = Path(tmpdir) / ".aztec.json"
        aztec_json.write_text(
            json.dumps({
                "entry_point_overrides": {
                    "src/custom_router.tsx": "router"
                },
                "extra_key_files": [
                    "src/constants/customSeeds.ts"
                ],
                "verifier_command": "echo verified"
            }),
            encoding="utf-8",
        )

        src_dir = Path(tmpdir) / "src"
        src_dir.mkdir(parents=True)
        (src_dir / "custom_router.tsx").write_text("export const Router = () => null;", encoding="utf-8")
        constants_dir = src_dir / "constants"
        constants_dir.mkdir()
        (constants_dir / "customSeeds.ts").write_text("export const SEEDS = [];", encoding="utf-8")

        cfg = load_project_aztec_config(tmpdir)
        assert cfg.get("verifier_command") == "echo verified"

        engine = LinkingEngine(config_overrides=cfg.get("entry_point_overrides", {}))
        graph = engine.build_graph(tmpdir)

        assert graph.entry_points.get("src/custom_router.tsx") == "router"

        manifest = engine.build_integration_manifest(
            graph,
            goal="Add new feature",
            extra_key_files=cfg.get("extra_key_files", []),
        )
        assert "src/custom_router.tsx" in manifest.mandatory_patch_targets
        assert "src/constants/customSeeds.ts" in manifest.mandatory_patch_targets


def test_integration_enforcer_detects_missing_patches():
    """Verify that missing mandatory coordinator patches are flagged as critical flaws."""
    manifest = IntegrationManifest(
        entry_points={"src/App.tsx": "react_root", "src/db/dexie.ts": "indexed_db"},
        mandatory_patch_targets=["src/App.tsx", "src/db/dexie.ts"],
        dependency_graph_summary="test summary",
    )

    # Case 1: missing both
    flaws = enforce_mandatory_patches(
        manifest=manifest,
        new_files={"src/components/NewModal.tsx": "code"},
        patches=[],
    )
    assert len(flaws) == 2
    assert any("src/App.tsx" in f for f in flaws)
    assert any("src/db/dexie.ts" in f for f in flaws)

    # Case 2: App.tsx patched, dexie.ts missing
    flaws2 = enforce_mandatory_patches(
        manifest=manifest,
        new_files={},
        patches=[
            ModularPatchItem(file="src/App.tsx", action="replace", replacement="code", concern="wiring")
        ],
    )
    assert len(flaws2) == 1
    assert "src/db/dexie.ts" in flaws2[0]

    # Case 3: All addressed
    flaws3 = enforce_mandatory_patches(
        manifest=manifest,
        new_files={},
        patches=[
            ModularPatchItem(file="src/App.tsx", action="replace", replacement="code", concern="wiring"),
            ModularPatchItem(file="src/db/dexie.ts", action="replace", replacement="code", concern="schema update"),
        ],
    )
    assert len(flaws3) == 0


@pytest.mark.asyncio
async def test_post_apply_verifier_runs_custom_command():
    """Verify PostApplyVerifier executes verification command and returns structured result."""
    with tempfile.TemporaryDirectory() as tmpdir:
        verifier = PostApplyVerifier(project_root=tmpdir)
        result: VerificationResult = await verifier.verify(custom_command="echo 'Compilation success'")
        assert result.success is True
        assert "Compilation success" in result.stdout
        assert result.error_count == 0
