"""
IR Builder — Canonicalization functor from raw LLM output to formal CodegenIR.

Constructs a fully typed, topologically sorted, and categorically verified CodegenIR
from raw synthesis outputs, performing static contract and cycle checks.
"""

from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import structlog

from aztec_circle.engine.ast_validator import ASTValidator
from aztec_circle.engine.codegen_ir import (
    CodegenFile,
    CodegenIR,
    CodegenPatch,
    ExportedSymbol,
    FileRole,
    ImportEdge,
)
from aztec_circle.engine.coherence_checker import CategoricalCoherenceChecker
from aztec_circle.engine.output_schema import sanitize_new_files_keys
from aztec_circle.engine.topo_sorter import TopologicalSorter

log = structlog.get_logger(__name__)

# TypeScript & JS Import regex
TS_IMPORT_RE = re.compile(
    r"""(?:import\s+(?:[^'"]+?\s+from\s+)?['"]([^'"]+)['"]"""
    r"""|require\s*\(\s*['"]([^'"]+)['"]\s*\))""",
    re.MULTILINE,
)

# Export pattern
EXPORT_PATTERN = re.compile(
    r"^export\s+(?:default\s+)?(?:async\s+)?(function|class|const|let|var|interface|type|enum)\s+([A-Za-z0-9_]+)",
    re.MULTILINE,
)


class IRBuilder:
    """
    Transforms raw JSON code draft into a formally verified CodegenIR.
    """

    def __init__(
        self,
        ast_validator: Optional[ASTValidator] = None,
        topo_sorter: Optional[TopologicalSorter] = None,
        coherence_checker: Optional[CategoricalCoherenceChecker] = None,
    ):
        self.ast_validator = ast_validator or ASTValidator()
        self.topo_sorter = topo_sorter or TopologicalSorter()
        self.coherence_checker = coherence_checker or CategoricalCoherenceChecker()

    def build(
        self,
        goal: str,
        architecture_overview: str,
        new_files: Dict[str, Any],
        patches: Optional[List[Dict[str, Any]]] = None,
        commands: Optional[List[Dict[str, Any]]] = None,
        existing_files: Optional[Dict[str, str]] = None,
    ) -> CodegenIR:
        """
        Build CodegenIR from raw new_files map and patch list.
        """
        clean_new_files, invalid_keys = sanitize_new_files_keys(new_files or {})
        parsed_patches: List[CodegenPatch] = []

        if patches:
            for p in patches:
                if isinstance(p, dict) and "file" in p:
                    parsed_patches.append(
                        CodegenPatch(
                            file=str(p["file"]).strip().lstrip("/\\").replace("\\", "/"),
                            action=str(p.get("action", "replace")),
                            start_line=p.get("start_line"),
                            end_line=p.get("end_line"),
                            replacement=p.get("replacement"),
                            concern=str(p.get("concern", "Code edit")),
                        )
                    )

        # 1. Construct CodegenFile objects
        codegen_files: Dict[str, CodegenFile] = {}
        type_contract_files: Dict[str, str] = {}
        all_content_for_coherence: Dict[str, str] = {}

        # Include existing type files for full context coherence
        if existing_files:
            for rel, content in existing_files.items():
                all_content_for_coherence[rel] = content
                role = self._classify_role(rel)
                if role == FileRole.TYPE_CONTRACT:
                    type_contract_files[rel] = content

        for rel_path, content_str in clean_new_files.items():
            role = self._classify_role(rel_path)
            exports = self._extract_exports(content_str)
            imports = self._extract_imports(rel_path, content_str)
            depends_on = [imp.target_file for imp in imports if not imp.is_external]

            cf = CodegenFile(
                rel_path=rel_path,
                content=content_str,
                role=role,
                line_count=len(content_str.splitlines()),
                exports=exports,
                imports=imports,
                depends_on=depends_on,
                is_new=True,
            )
            codegen_files[rel_path] = cf
            all_content_for_coherence[rel_path] = content_str

            if role == FileRole.TYPE_CONTRACT:
                type_contract_files[rel_path] = content_str

        # 2. Build graph for topological sorting
        all_nodes = list(codegen_files.keys())
        # Also include modified files in the sort
        for p in parsed_patches:
            if p.file not in all_nodes and p.file:
                all_nodes.append(p.file)

        edges: Dict[str, List[str]] = {}
        for rel_path, cfile in codegen_files.items():
            edges[rel_path] = [dep for dep in cfile.depends_on if dep in all_nodes]

        sorted_order, cycles = self.topo_sorter.sort(all_nodes, edges)

        # 3. Check layer discipline
        node_roles: Dict[str, FileRole] = {
            rel: codegen_files[rel].role for rel in codegen_files
        }
        for p in parsed_patches:
            if p.file not in node_roles:
                node_roles[p.file] = self._classify_role(p.file)

        layer_violations = self.topo_sorter.check_layer_violations(node_roles, edges)

        # 4. Check categorical type coherence
        contracts = self.coherence_checker.extract_contracts(type_contract_files)
        coherence_violations = self.coherence_checker.check_coherence(
            contracts,
            all_content_for_coherence,
        )

        all_violations: List[str] = list(layer_violations)
        for cv in coherence_violations:
            all_violations.append(cv.format_message())
        for ik in invalid_keys:
            all_violations.append(f"INVALID FILE PATH KEY: '{ik}' is not a valid relative path.")

        cycle_errors: List[str] = []
        for cycle in cycles:
            cycle_str = " -> ".join(cycle)
            cycle_errors.append(f"CYCLIC IMPORT DEPENDENCY: {cycle_str}")

        coherence_score = self.coherence_checker.compute_coherence_score(
            coherence_violations,
            len(all_content_for_coherence),
        )

        is_valid = (len(cycle_errors) == 0) and (coherence_score >= 0.75)

        return CodegenIR(
            goal=goal,
            architecture_overview=architecture_overview,
            files=codegen_files,
            patches=parsed_patches,
            commands=commands or [],
            topo_order=sorted_order,
            contract_violations=all_violations,
            cycle_errors=cycle_errors,
            coherence_score=coherence_score,
            is_valid=is_valid,
        )

    def _classify_role(self, rel_path: str) -> FileRole:
        lower = rel_path.lower().replace("\\", "/")

        if lower.endswith(("package.json", "tsconfig.json", "vite.config.ts", "tailwind.config.js")):
            return FileRole.CONFIG
        if "/types/" in lower or lower.startswith("types/") or lower.endswith((".types.ts", ".d.ts")):
            return FileRole.TYPE_CONTRACT
        if "/engine/" in lower or lower.startswith("engine/"):
            return FileRole.DOMAIN_ENGINE
        if "/store/" in lower or lower.startswith("store/"):
            return FileRole.STATE_STORE
        if "/hooks/" in lower or lower.startswith("hooks/"):
            return FileRole.HOOK
        if "/atoms/" in lower or lower.startswith("atoms/"):
            return FileRole.UI_ATOM
        if "/components/" in lower or lower.startswith("components/"):
            return FileRole.UI_COMPONENT
        if any(marker in lower for marker in ("app.tsx", "main.tsx", "routes.", "router.")):
            return FileRole.COORDINATOR
        if any(marker in lower for marker in (".test.", ".spec.", "/tests/")):
            return FileRole.TEST
        if lower.startswith("backend/") or lower.endswith((".py", ".php")):
            return FileRole.BACKEND
        if lower.endswith(".sql") or "/migrations/" in lower:
            return FileRole.MIGRATION

        return FileRole.UNKNOWN

    def _extract_exports(self, content: str) -> List[ExportedSymbol]:
        exports: List[ExportedSymbol] = []
        for match in EXPORT_PATTERN.finditer(content):
            kind = match.group(1)
            name = match.group(2)
            exports.append(ExportedSymbol(name=name, kind=kind))
        return exports

    def _extract_imports(self, rel_path: str, content: str) -> List[ImportEdge]:
        edges: List[ImportEdge] = []
        importer_dir = os.path.dirname(rel_path)

        for match in TS_IMPORT_RE.finditer(content):
            specifier = match.group(1) or match.group(2)
            if not specifier:
                continue

            if specifier.startswith("."):
                # Relative import
                resolved = os.path.normpath(os.path.join(importer_dir, specifier)).replace("\\", "/")
                # Normalize candidate extension
                if not any(resolved.endswith(ext) for ext in (".ts", ".tsx", ".js", ".jsx")):
                    resolved_cand = resolved + ".ts"
                else:
                    resolved_cand = resolved

                edges.append(
                    ImportEdge(
                        source_file=rel_path,
                        target_file=resolved_cand,
                        is_external=False,
                    )
                )
            else:
                edges.append(
                    ImportEdge(
                        source_file=rel_path,
                        target_file=specifier,
                        is_external=True,
                    )
                )

        return edges
