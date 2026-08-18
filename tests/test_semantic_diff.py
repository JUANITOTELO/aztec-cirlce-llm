"""
Unit tests for SemanticDiffVerifier (natural transformation safety).
"""

import pytest
from aztec_circle.engine.codegen_ir import CodegenFile, CodegenIR, CodegenPatch, FileRole
from aztec_circle.engine.linking_engine import DependencyGraph, FileNode
from aztec_circle.engine.semantic_diff import SemanticDiffVerifier


def test_semantic_diff_detects_breaking_export_deletion():
    verifier = SemanticDiffVerifier()

    # Pre-patch graph: auth.ts exports 'useAuth' and 'login', consumed by App.tsx
    pre_graph = DependencyGraph(
        nodes={
            "src/hooks/useAuth.ts": FileNode(
                rel_path="src/hooks/useAuth.ts",
                exports=["useAuth", "login"],
                imported_by=["src/App.tsx"],
            ),
            "src/App.tsx": FileNode(
                rel_path="src/App.tsx",
                imports=["src/hooks/useAuth.ts"],
            ),
        }
    )

    # Proposed patch: replaces useAuth.ts but deletes 'login'
    ir = CodegenIR(
        goal="Refactor auth",
        architecture_overview="Auth refactor",
        patches=[
            CodegenPatch(
                file="src/hooks/useAuth.ts",
                action="replace",
                replacement="export function useAuth() { return {}; }",  # 'login' is gone!
                concern="Refactor",
            )
        ],
    )

    report = verifier.verify_transformation("/fake/root", pre_graph, ir)
    assert not report.is_safe
    assert len(report.removed_exports) > 0
    assert "login" in report.removed_exports[0]


def test_semantic_diff_detects_orphaned_new_files():
    verifier = SemanticDiffVerifier()
    pre_graph = DependencyGraph(nodes={})

    # New file created (UI component) with zero inbound references
    ir = CodegenIR(
        goal="Add orphaned modal",
        architecture_overview="Modal",
        files={
            "src/components/OrphanModal.tsx": CodegenFile(
                rel_path="src/components/OrphanModal.tsx",
                content="export const OrphanModal = () => null;",
                role=FileRole.UI_COMPONENT,
            )
        },
        patches=[],
    )

    report = verifier.verify_transformation("/fake/root", pre_graph, ir)
    assert len(report.orphaned_modules) > 0
    assert "OrphanModal.tsx" in report.orphaned_modules[0]
