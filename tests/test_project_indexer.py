"""
Unit tests for ProjectIndexer.
"""

import json
from aztec_circle.engine.project_indexer import ProjectIndexer, ProjectIndex, FileIndex


def test_project_indexer_empty_dir(tmp_path):
    indexer = ProjectIndexer()
    index = indexer.build(str(tmp_path))
    assert index.total_files == 0
    assert index.total_lines == 0
    assert index.file_tree == []


def test_project_indexer_scans_and_extracts_exports(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "App.tsx").write_text("export default function App() { return <div>App</div>; }\nexport const APP_VERSION = '1.0.0';\n", encoding="utf-8")
    
    engine = src / "engine"
    engine.mkdir()
    (engine / "Rig.ts").write_text("export class Dummy13Rig {}\nexport interface RigConfig {}\nexport const DEFAULT_CONFIG = {};\n", encoding="utf-8")

    indexer = ProjectIndexer()
    index = indexer.build(str(tmp_path))

    assert index.total_files == 2
    assert index.total_lines > 0
    assert "src/App.tsx" in index.file_tree
    assert "src/engine/Rig.ts" in index.file_tree

    app_file = index.get_file("src/App.tsx")
    assert app_file is not None
    assert "App" in app_file.exports or "APP_VERSION" in app_file.exports

    rig_file = index.get_file("src/engine/Rig.ts")
    assert rig_file is not None
    assert "Dummy13Rig" in rig_file.exports


def test_project_indexer_to_prompt_context(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "Button.tsx").write_text("export const Button = () => null;\n", encoding="utf-8")

    indexer = ProjectIndexer()
    index = indexer.build(str(tmp_path))
    context = indexer.to_prompt_context(index)

    assert "PROJECT ROOT:" in context
    assert "src/Button.tsx" in context
    assert "exports: Button" in context
