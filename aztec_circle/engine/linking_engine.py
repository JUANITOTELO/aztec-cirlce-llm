"""
LinkingEngine — Abstract Holistic Dependency & Integration Graph for Aztec.

Performs static analysis of any project codebase to build a language-agnostic
dependency graph and auto-detect integration entry points that must be patched
when new modules are added.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog

from aztec_circle.engine.scaffolder import find_project_root

log = structlog.get_logger(__name__)

# ── Language-agnostic import extractors ─────────────────────────────────────

TS_IMPORT_RE = re.compile(
    r"""(?:import\s+(?:[^'"]+?\s+from\s+)?['"]([^'"]+)['"]"""
    r"""|require\s*\(\s*['"]([^'"]+)['"]\s*\))""",
    re.MULTILINE,
)

PYTHON_IMPORT_RE = re.compile(
    r"""^(?:from\s+([\w.]+)\s+import|import\s+([\w.,\s]+))""",
    re.MULTILINE,
)

PHP_INCLUDE_RE = re.compile(
    r"""(?:require|include)(?:_once)?\s*\(?['"](.*?)['"]\)?""",
    re.MULTILINE,
)

EXPORT_PATTERN = re.compile(
    r"^export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var|interface|type|enum)\s+([A-Za-z0-9_]+)",
    re.MULTILINE,
)

# ── Entry-point heuristics (auto-detect) ────────────────────────────────────

COORDINATOR_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # React/Vite/Next root coordinators
    (re.compile(r"\bApp\.(tsx?|jsx?)\b", re.IGNORECASE), "react_root"),
    (re.compile(r"\bmain\.(tsx?|jsx?)\b", re.IGNORECASE), "react_entry"),
    (re.compile(r"\b(router|routes|navigation)\.(tsx?|jsx?|ts|js)\b", re.IGNORECASE), "router"),
    # Type index / barrel exports
    (re.compile(r"\btypes/(?:index|store|models)\.ts\b", re.IGNORECASE), "type_barrel"),
    (re.compile(r"\bindex\.(ts|tsx|js|jsx)\b", re.IGNORECASE), "barrel_export"),
    # State / Storage / DB
    (re.compile(r"\b(store|state|slices?|atoms?)\.(ts|tsx|js|jsx)\b", re.IGNORECASE), "state_store"),
    (re.compile(r"\b(dexie|db|database|sqlite|indexeddb)\.(ts|js)\b", re.IGNORECASE), "indexed_db"),
    (re.compile(r"\bschema\.sql\b", re.IGNORECASE), "db_schema"),
    (re.compile(r"\bmigrations?/", re.IGNORECASE), "db_migration"),
    # Backend entries
    (re.compile(r"\bindex\.php\b", re.IGNORECASE), "php_entry"),
    (re.compile(r"\b(app|main|server)\.py\b", re.IGNORECASE), "python_entry"),
    # Mock / seed data
    (re.compile(r"\bmock(?:Data|s|Categories|Variants)?\.(ts|tsx|js|json)\b", re.IGNORECASE), "seed_data"),
    (re.compile(r"\bconstants/mock", re.IGNORECASE), "seed_data"),
    # Navigation / layout
    (re.compile(r"\b(Header|Navbar|Sidebar|Layout)\.(tsx?|jsx?)\b", re.IGNORECASE), "nav_coordinator"),
]


def load_project_aztec_config(project_root: str) -> Dict[str, Any]:
    """
    Load project-specific .aztec.json configuration if present.
    Supports entry_point_overrides, extra_key_files, verifier_command, etc.
    """
    root = find_project_root(project_root) or project_root
    config_path = os.path.join(root, ".aztec.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except Exception as e:
            log.warning("linking_engine.config_load_failed", path=config_path, error=str(e))
    return {}


@dataclass
class FileNode:
    """Metadata and dependency graph edges for a single file."""
    rel_path: str
    imports: List[str] = field(default_factory=list)
    imported_by: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    entry_point_roles: List[str] = field(default_factory=list)
    line_count: int = 0


@dataclass
class DependencyGraph:
    """Directed dependency graph across project source files."""
    nodes: Dict[str, FileNode] = field(default_factory=dict)
    entry_points: Dict[str, str] = field(default_factory=dict)  # rel_path -> primary role


@dataclass
class IntegrationManifest:
    """
    Describes mandatory integration targets and architectural hotspots
    for modular feature additions.
    """
    entry_points: Dict[str, str]
    mandatory_patch_targets: List[str]
    dependency_graph_summary: str
    hotspot_files: List[str] = field(default_factory=list)


class LinkingEngine:
    """
    Language-agnostic linking and static dependency graph analysis engine.
    Discovers integration entry points and generates grounding manifests
    to prevent orphaned modular code.
    """

    EXCLUDED_DIRS = frozenset([
        "node_modules",
        ".git",
        "dist",
        "build",
        "__pycache__",
        ".vite",
        ".next",
        ".pytest_cache",
        "coverage",
    ])

    INCLUDED_EXTS = frozenset([
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".json",
        ".css",
        ".py",
        ".php",
        ".sql",
        ".html",
        ".lean",
    ])

    MANDATORY_ROLES = frozenset([
        "react_root",
        "router",
        "state_store",
        "indexed_db",
        "type_barrel",
        "db_schema",
        "seed_data",
        "nav_coordinator",
        "php_entry",
        "python_entry",
    ])

    def __init__(self, config_overrides: Optional[Dict[str, str]] = None):
        self.config_overrides = config_overrides or {}

    def build_graph(self, project_root: str) -> DependencyGraph:
        """Scan project_root and construct a complete DependencyGraph."""
        root = find_project_root(project_root) or project_root
        graph = DependencyGraph()

        if not os.path.exists(root):
            return graph

        # 1. First pass: analyze individual files
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                d for d in dirnames
                if d not in self.EXCLUDED_DIRS and not d.startswith(".")
            ]

            for filename in sorted(filenames):
                _, ext = os.path.splitext(filename)
                if ext.lower() not in self.INCLUDED_EXTS:
                    continue

                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root).replace("\\", "/")

                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                    node = self._analyze_file(rel_path, content, root)
                    graph.nodes[rel_path] = node
                except Exception as exc:
                    log.debug("linking_engine.file_analyze_failed", path=rel_path, error=str(exc))
                    continue

        # 2. Second pass: build reverse edges (imported_by)
        for rel_path, node in graph.nodes.items():
            for imported_rel in node.imports:
                if imported_rel in graph.nodes:
                    if rel_path not in graph.nodes[imported_rel].imported_by:
                        graph.nodes[imported_rel].imported_by.append(rel_path)

        # 3. Third pass: assign entry point roles (config overrides take priority)
        for rel_path, role in self.config_overrides.items():
            clean_rel = rel_path.lstrip("/\\").replace("\\", "/")
            if clean_rel in graph.nodes:
                graph.entry_points[clean_rel] = role
                if role not in graph.nodes[clean_rel].entry_point_roles:
                    graph.nodes[clean_rel].entry_point_roles.append(role)

        for rel_path, node in graph.nodes.items():
            if rel_path not in graph.entry_points and node.entry_point_roles:
                graph.entry_points[rel_path] = node.entry_point_roles[0]

        return graph

    def _analyze_file(self, rel_path: str, content: str, project_root: str) -> FileNode:
        """Extract imports, exports, and matching coordinator roles for a file."""
        ext = os.path.splitext(rel_path)[1].lower()
        imports: List[str] = []

        if ext in {".ts", ".tsx", ".js", ".jsx"}:
            for match in TS_IMPORT_RE.finditer(content):
                specifier = match.group(1) or match.group(2)
                if specifier:
                    resolved = self._resolve_ts_import(specifier, rel_path, project_root)
                    if resolved:
                        imports.append(resolved)
        elif ext == ".py":
            for match in PYTHON_IMPORT_RE.finditer(content):
                pkg = match.group(1) or match.group(2)
                if pkg:
                    imports.append(pkg.strip().split(".")[0])
        elif ext == ".php":
            for match in PHP_INCLUDE_RE.finditer(content):
                inc = match.group(1)
                if inc:
                    imports.append(inc.strip())

        # Extract symbols
        exports = EXPORT_PATTERN.findall(content)

        # Detect coordinator roles
        roles: List[str] = []
        for pattern, role in COORDINATOR_PATTERNS:
            if pattern.search(rel_path):
                if role not in roles:
                    roles.append(role)

        return FileNode(
            rel_path=rel_path,
            imports=list(dict.fromkeys(imports)),
            exports=list(dict.fromkeys(exports))[:12],
            entry_point_roles=roles,
            line_count=len(content.splitlines()),
        )

    def _resolve_ts_import(self, specifier: str, importer_rel: str, project_root: str) -> Optional[str]:
        """Resolve a relative TypeScript/JavaScript import path to a relative project path."""
        if not specifier.startswith("."):
            return None  # External npm dependency

        importer_dir = os.path.dirname(os.path.join(project_root, importer_rel))
        resolved_base = os.path.normpath(os.path.join(importer_dir, specifier))
        rel_resolved = os.path.relpath(resolved_base, project_root).replace("\\", "/")

        candidate_exts = ["", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.tsx", "/index.js"]
        for ext in candidate_exts:
            candidate = rel_resolved + ext
            if os.path.exists(os.path.join(project_root, candidate)):
                return candidate.replace("\\", "/")

        return rel_resolved

    def build_integration_manifest(
        self,
        graph: DependencyGraph,
        goal: str = "",
        extra_key_files: Optional[List[str]] = None,
    ) -> IntegrationManifest:
        """
        Produce a comprehensive IntegrationManifest detailing mandatory patch targets,
        hotspot files, and entry-point bindings.
        """
        mandatory: List[str] = []
        for rel_path, role in graph.entry_points.items():
            if role in self.MANDATORY_ROLES:
                if rel_path not in mandatory:
                    mandatory.append(rel_path)

        if extra_key_files:
            for extra in extra_key_files:
                clean_extra = extra.lstrip("/\\").replace("\\", "/")
                if clean_extra in graph.nodes and clean_extra not in mandatory:
                    mandatory.append(clean_extra)

        # Sort hotspots by number of dependents (most imported files)
        hotspots = sorted(
            graph.nodes.values(),
            key=lambda n: len(n.imported_by),
            reverse=True,
        )[:8]

        summary_lines = [
            f"DEPENDENCY GRAPH ({len(graph.nodes)} files analyzed):",
            "",
            "ENTRY POINTS & COORDINATORS (Auto-Detected + Overrides):",
        ]
        for rel, role in sorted(graph.entry_points.items()):
            node = graph.nodes.get(rel)
            imp_count = len(node.imported_by) if node else 0
            summary_lines.append(f"  [{role}] {rel}  (imported by {imp_count} files)")

        if hotspots:
            summary_lines.extend(["", "INTEGRATION HOTSPOTS (High risk of breaking dependencies):"])
            for h in hotspots:
                dep_preview = ", ".join(h.imported_by[:3])
                if len(h.imported_by) > 3:
                    dep_preview += "..."
                summary_lines.append(f"  {h.rel_path}  ← imported by {len(h.imported_by)} files: {dep_preview}")

        summary_lines.extend(["", "MANDATORY INTEGRATION TARGETS (Must be wired/patched if relevant to feature):"])
        for m in mandatory:
            role = graph.entry_points.get(m, "custom_anchor")
            summary_lines.append(f"  ✦ {m}  [{role}]")

        return IntegrationManifest(
            entry_points=dict(graph.entry_points),
            mandatory_patch_targets=mandatory,
            dependency_graph_summary="\n".join(summary_lines),
            hotspot_files=[h.rel_path for h in hotspots],
        )

    def to_prompt_context(self, manifest: IntegrationManifest) -> str:
        """Render manifest into token-efficient prompt context string."""
        return manifest.dependency_graph_summary
