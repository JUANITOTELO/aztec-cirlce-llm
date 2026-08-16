"""
Project Indexer for Aztec Incremental Edit Engine.
Builds compact, token-efficient summaries of codebase structure and symbol exports.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from aztec_circle.engine.scaffolder import find_project_root, detect_project_ecosystem

EXPORT_PATTERN = re.compile(
    r"^export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|var|interface|type|enum)\s+([A-Za-z0-9_]+)",
    re.MULTILINE,
)


@dataclass
class FileIndex:
    """Metadata for an indexed source file."""
    rel_path: str
    line_count: int
    size_bytes: int
    exports: List[str] = field(default_factory=list)


@dataclass
class ProjectIndex:
    """Compact structured summary of a project's files and exports."""
    project_root: str
    ecosystem: str
    total_files: int
    total_lines: int
    file_indices: List[FileIndex] = field(default_factory=list)

    @property
    def file_tree(self) -> List[str]:
        return [f.rel_path for f in self.file_indices]

    def get_file(self, rel_path: str) -> Optional[FileIndex]:
        for f in self.file_indices:
            if f.rel_path == rel_path or f.rel_path.lstrip("/\\") == rel_path.lstrip("/\\"):
                return f
        return None


class ProjectIndexer:
    """
    Scans project directory and builds an ultra-compact codebase summary
    optimized for low token consumption in LLM prompts.
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
        ".html",
        ".md",
    ])

    def __init__(self, max_files: int = 100):
        self.max_files = max_files

    def build(self, project_dir: str) -> ProjectIndex:
        """Scan project_dir and construct ProjectIndex."""
        root = find_project_root(project_dir)
        ecosystem = detect_project_ecosystem(root)
        indices: List[FileIndex] = []
        total_lines = 0

        if not os.path.exists(root):
            return ProjectIndex(
                project_root=root,
                ecosystem=ecosystem,
                total_files=0,
                total_lines=0,
                file_indices=[],
            )

        for dirpath, dirnames, filenames in os.walk(root):
            # Prune excluded directories in-place
            dirnames[:] = [d for d in dirnames if d not in self.EXCLUDED_DIRS and not d.startswith(".")]

            for filename in sorted(filenames):
                _, ext = os.path.splitext(filename)
                if ext.lower() not in self.INCLUDED_EXTS:
                    continue

                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root).replace("\\", "/")

                try:
                    stat = os.stat(full_path)
                    with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()

                    lines = content.splitlines()
                    line_count = len(lines)
                    total_lines += line_count

                    # Extract exports from file
                    exports = EXPORT_PATTERN.findall(content)
                    # Deduplicate preserving order
                    unique_exports = list(dict.fromkeys(exports))

                    indices.append(
                        FileIndex(
                            rel_path=rel_path,
                            line_count=line_count,
                            size_bytes=stat.st_size,
                            exports=unique_exports[:8],  # Keep top 8 exports for brevity
                        )
                    )

                    if len(indices) >= self.max_files:
                        break
                except Exception:
                    continue

        # Sort indices: src/ files first, then alphabetically
        indices.sort(key=lambda f: (0 if f.rel_path.startswith("src/") else 1, f.rel_path))

        return ProjectIndex(
            project_root=root,
            ecosystem=ecosystem,
            total_files=len(indices),
            total_lines=total_lines,
            file_indices=indices,
        )

    def to_prompt_context(self, index: ProjectIndex) -> str:
        """
        Renders index into a compact, human-readable prompt string (~300-500 tokens).
        """
        lines = [
            f"PROJECT ROOT: {index.project_root}",
            f"ECOSYSTEM: {index.ecosystem} ({index.total_files} source files, {index.total_lines} total lines)",
            "SOURCE TREE & EXPORTS:",
        ]

        for f in index.file_indices:
            export_str = f" [exports: {', '.join(f.exports)}]" if f.exports else ""
            lines.append(f"  - {f.rel_path} ({f.line_count}L){export_str}")

        return "\n".join(lines)
