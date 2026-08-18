"""
Semantic Diff Verifier for Aztec Decision Circle.

Verifies natural transformations across code mutations:
Compares pre-patch and post-patch dependency graphs to detect:
1. Deleted/altered exports that break existing consumers.
2. Newly created orphaned modules with zero inbound references.
3. Newly introduced cyclic dependencies.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import structlog

from aztec_circle.engine.codegen_ir import CodegenIR
from aztec_circle.engine.linking_engine import DependencyGraph, LinkingEngine

log = structlog.get_logger(__name__)


@dataclass
class SemanticDiffReport:
    """Outcome of a pre/post-patch semantic transformation check."""
    is_safe: bool
    removed_exports: List[str] = field(default_factory=list)
    orphaned_modules: List[str] = field(default_factory=list)
    new_cycles: List[str] = field(default_factory=list)
    critical_flaws: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SemanticDiffVerifier:
    """
    Analyzes pre-patch and post-patch dependency graphs to verify semantic safety.
    """

    def __init__(self, linking_engine: Optional[LinkingEngine] = None):
        self.linking_engine = linking_engine or LinkingEngine()

    def verify_transformation(
        self,
        project_root: str,
        pre_graph: DependencyGraph,
        ir: CodegenIR,
    ) -> SemanticDiffReport:
        """
        Evaluate proposed IR against existing pre-patch dependency graph.
        """
        critical_flaws: List[str] = []
        warnings: List[str] = []
        removed_exports: List[str] = []
        orphaned_modules: List[str] = []

        # 1. Check for removed exports from existing files
        for patch in ir.patches:
            clean_file = patch.file.lstrip("/\\").replace("\\", "/")
            if clean_file in pre_graph.nodes:
                old_node = pre_graph.nodes[clean_file]
                # If existing node has dependents, check if replacement removes key exports
                if old_node.imported_by and patch.action == "replace" and patch.replacement:
                    new_text = patch.replacement
                    for exp in old_node.exports:
                        # Check if export symbol still present in new content
                        if exp not in new_text and f"export {exp}" not in new_text:
                            msg = (
                                f"BREAKING EXPORT DELETION: Patch to '{clean_file}' removes export '{exp}' "
                                f"which is required by {len(old_node.imported_by)} file(s): "
                                f"{', '.join(old_node.imported_by[:3])}"
                            )
                            removed_exports.append(msg)
                            critical_flaws.append(msg)

        # 2. Check for orphaned new files
        # A new UI component or store file should ideally be referenced by another new file or an existing coordinator patch
        patched_files_set = {p.file.lstrip("/\\").replace("\\", "/") for p in ir.patches}

        for new_rel, cfile in ir.files.items():
            if cfile.role in ("ui_component", "state_store", "hook"):
                # Check if any other new file imports it, or if any patched coordinator imports it
                imported_by_others = False
                base_name = os.path.splitext(os.path.basename(new_rel))[0]

                # Check in other new files
                for other_rel, other_file in ir.files.items():
                    if other_rel != new_rel and base_name in other_file.content:
                        imported_by_others = True
                        break

                # Check in patch replacements
                if not imported_by_others:
                    for patch in ir.patches:
                        if patch.replacement and base_name in patch.replacement:
                            imported_by_others = True
                            break

                if not imported_by_others:
                    msg = (
                        f"POTENTIALLY ORPHANED MODULE: New file '{new_rel}' ({cfile.role.value}) "
                        f"is not imported or rendered by any new file or coordinator patch."
                    )
                    orphaned_modules.append(msg)
                    warnings.append(msg)

        # 3. Propagate cycle errors from IR
        new_cycles = list(ir.cycle_errors)
        for cy in new_cycles:
            critical_flaws.append(cy)

        is_safe = len(critical_flaws) == 0

        return SemanticDiffReport(
            is_safe=is_safe,
            removed_exports=removed_exports,
            orphaned_modules=orphaned_modules,
            new_cycles=new_cycles,
            critical_flaws=critical_flaws,
            warnings=warnings,
        )
