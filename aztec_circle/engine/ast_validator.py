"""
AST Validator — Grammar-aware syntax and structural validator for Aztec code patches.

Uses tree-sitter grammars (TypeScript, TSX, Python) with graceful lightweight AST fallbacks
to verify syntactic correctness before writing code to disk.
"""

from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass, field
from typing import Any, List, Optional
import structlog

log = structlog.get_logger(__name__)


@dataclass
class ASTValidationResult:
    """Outcome of an AST syntactic validation pass."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    has_error_nodes: bool = False
    engine: str = "tree-sitter"


class ASTValidator:
    """
    Validates code syntax and structure prior to filesystem write.
    Uses tree-sitter for TS/TSX/Python when installed, with standard library AST fallback.
    """

    def __init__(self):
        self._tree_sitter_available = False
        self._parsers: dict[str, Any] = {}
        self._init_tree_sitter()

    def _init_tree_sitter(self) -> None:
        try:
            from tree_sitter import Language, Parser
            import tree_sitter_python as tspython
            import tree_sitter_typescript as tstypescript

            ts_lang = Language(tstypescript.language_typescript())
            tsx_lang = Language(tstypescript.language_tsx())
            py_lang = Language(tspython.language())

            self._parsers["ts"] = Parser(ts_lang)
            self._parsers["tsx"] = Parser(tsx_lang)
            self._parsers["jsx"] = Parser(tsx_lang)
            self._parsers["js"] = Parser(ts_lang)
            self._parsers["py"] = Parser(py_lang)
            self._tree_sitter_available = True
            log.debug("ast_validator.tree_sitter_initialized")
        except Exception as exc:
            self._tree_sitter_available = False
            log.debug("ast_validator.tree_sitter_unavailable_fallback", error=str(exc))

    def validate(self, content: str, file_path: str) -> ASTValidationResult:
        """
        Validate source code text for syntax errors.

        Args:
            content: Raw source code string.
            file_path: Relative or absolute path (used to determine language extension).

        Returns:
            ASTValidationResult indicating if the code parses cleanly.
        """
        if not content.strip():
            return ASTValidationResult(is_valid=True)

        _, ext = os.path.splitext(file_path)
        ext_clean = ext.lower().lstrip(".")

        if self._tree_sitter_available and ext_clean in self._parsers:
            return self._validate_with_tree_sitter(content, ext_clean)

        # Fallback validation
        if ext_clean == "py":
            return self._validate_python_stdlib(content)
        elif ext_clean in ("ts", "tsx", "js", "jsx"):
            return self._validate_js_heuristic(content)

        return ASTValidationResult(is_valid=True, engine="passthrough")

    def _validate_with_tree_sitter(self, content: str, ext: str) -> ASTValidationResult:
        parser = self._parsers.get(ext)
        if not parser:
            return ASTValidationResult(is_valid=True, engine="tree-sitter")

        try:
            encoded = content.encode("utf-8")
            tree = parser.parse(encoded)
            root = tree.root_node

            if not root.has_error:
                return ASTValidationResult(is_valid=True, engine="tree-sitter")

            # Collect detailed syntax error locations
            errors: List[str] = []
            self._collect_error_nodes(root, errors, content)

            if not errors:
                errors.append("Syntax error detected in AST structure.")

            return ASTValidationResult(
                is_valid=False,
                errors=errors[:10],
                has_error_nodes=True,
                engine="tree-sitter",
            )
        except Exception as exc:
            return ASTValidationResult(
                is_valid=False,
                errors=[f"tree-sitter parser exception: {exc}"],
                has_error_nodes=True,
                engine="tree-sitter",
            )

    def _collect_error_nodes(self, node: Any, errors: List[str], content: str) -> None:
        if node.is_error or node.is_missing:
            start_row, start_col = node.start_point
            end_row, end_col = node.end_point
            snippet = node.text.decode("utf-8", errors="replace")[:60] if hasattr(node, "text") else ""
            errors.append(
                f"Syntax ERROR at L{start_row + 1}:C{start_col + 1} to L{end_row + 1}:C{end_col + 1}: '{snippet}'"
            )
        for child in node.children:
            self._collect_error_nodes(child, errors, content)

    def _validate_python_stdlib(self, content: str) -> ASTValidationResult:
        try:
            ast.parse(content)
            return ASTValidationResult(is_valid=True, engine="python-ast")
        except SyntaxError as exc:
            return ASTValidationResult(
                is_valid=False,
                errors=[f"Python SyntaxError at line {exc.lineno}: {exc.msg}"],
                has_error_nodes=True,
                engine="python-ast",
            )

    def _validate_js_heuristic(self, content: str) -> ASTValidationResult:
        """Lightweight balanced brace and delimiter validator when tree-sitter is unavailable."""
        errors: List[str] = []
        stack: List[tuple[str, int]] = []
        pairs = {")": "(", "}": "{", "]": "["}
        lines = content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            # Skip full-line comments
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue

            for char in line:
                if char in "({[":
                    stack.append((char, line_num))
                elif char in ")}]":
                    if not stack:
                        errors.append(f"Unmatched closing '{char}' at line {line_num}")
                        break
                    last_open, open_line = stack.pop()
                    if pairs[char] != last_open:
                        errors.append(f"Mismatched '{last_open}' (line {open_line}) closed by '{char}' at line {line_num}")
                        break

        if stack and len(errors) < 5:
            for unclosed, open_line in stack[-3:]:
                errors.append(f"Unclosed delimiter '{unclosed}' opened at line {open_line}")

        return ASTValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            has_error_nodes=len(errors) > 0,
            engine="heuristic-delimiter",
        )
