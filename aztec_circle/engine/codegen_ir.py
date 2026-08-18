"""
CodegenIR — Formal Typed Intermediate Representation for Aztec Code Generation.

Treats the project codebase as a mathematical category:
- Objects: Source files and module definitions
- Morphisms: Dependency edges and typed import bindings
- Functors: Category-preserving maps from ground-truth type contracts to implementations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class FileRole(str, Enum):
    """Architectural classification of a source file."""
    CONFIG = "config"                 # package.json, tsconfig.json, vite.config.ts
    TYPE_CONTRACT = "type_contract"   # src/types/*.ts — ground-truth interfaces
    DOMAIN_ENGINE = "domain_engine"   # src/engine/*.ts — pure logic, math, zero JSX
    STATE_STORE = "state_store"       # src/store/*.ts — state slices & persistence
    HOOK = "hook"                     # src/hooks/*.ts — React state/effect hooks
    UI_ATOM = "ui_atom"               # src/atoms/*.tsx — atomic UI primitives
    UI_COMPONENT = "ui_component"     # src/components/**/*.tsx — composite panels
    COORDINATOR = "coordinator"       # App.tsx, main.tsx, routers, top layout
    TEST = "test"                     # *.test.ts, *.spec.ts, backend test scripts
    BACKEND = "backend"               # backend/*.py, backend/*.php, server.py
    MIGRATION = "migration"           # *.sql, migrations/
    UNKNOWN = "unknown"


@dataclass
class ExportedSymbol:
    """Represents a formally declared export in a source file."""
    name: str
    kind: str  # "interface" | "type" | "function" | "const" | "class" | "enum"
    signature: str = ""
    line_number: Optional[int] = None


@dataclass
class ImportEdge:
    """Represents a directed dependency morphism: source_file -> target_file."""
    source_file: str
    target_file: str
    symbols: List[str] = field(default_factory=list)
    is_external: bool = False  # True for npm/pip third-party modules


@dataclass
class CodegenFile:
    """Represents a generated or modified file within the IR."""
    rel_path: str
    content: str
    role: FileRole
    line_count: int = 0
    exports: List[ExportedSymbol] = field(default_factory=list)
    imports: List[ImportEdge] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    is_new: bool = True


@dataclass
class CodegenPatch:
    """Represents a structured atomic patch operation on an existing file."""
    file: str
    action: str  # "replace" | "insert_before" | "insert_after" | "create" | "delete"
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    replacement: Optional[str] = None
    concern: str = "Code edit"
    introduces_symbols: List[str] = field(default_factory=list)
    removes_symbols: List[str] = field(default_factory=list)
    modifies_symbols: List[str] = field(default_factory=list)


@dataclass
class CodegenIR:
    """
    The complete, formally-typed Intermediate Representation of a synthesis cycle.
    Guarantees structural, topological, and categorical integrity before filesystem application.
    """
    goal: str
    architecture_overview: str
    files: Dict[str, CodegenFile] = field(default_factory=dict)
    patches: List[CodegenPatch] = field(default_factory=list)
    commands: List[Dict[str, Any]] = field(default_factory=list)
    topo_order: List[str] = field(default_factory=list)
    contract_violations: List[str] = field(default_factory=list)
    cycle_errors: List[str] = field(default_factory=list)
    coherence_score: float = 1.0  # 0.0 to 1.0
    is_valid: bool = True

    @property
    def total_files(self) -> int:
        return len(self.files)

    @property
    def total_patches(self) -> int:
        return len(self.patches)

    def summary(self) -> str:
        status = "VALID" if self.is_valid and not self.cycle_errors else "INVALID"
        return (
            f"CodegenIR[{status}]: {len(self.files)} files, {len(self.patches)} patches, "
            f"coherence={self.coherence_score:.2f}, cycles={len(self.cycle_errors)}, "
            f"violations={len(self.contract_violations)}"
        )
