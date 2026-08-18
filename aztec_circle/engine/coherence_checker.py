"""
Categorical Coherence Checker for Aztec Decision Circle.

Verifies functor-style type contract preservation:
All implementation files (hooks, engines, components) must be valid structure-preserving
maps from the ground-truth contract category (src/types/ interfaces & models).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ContractViolation:
    """Represents a discrepancy between a declared type contract and an implementation."""
    file: str
    symbol: str
    expected_signature: str
    actual_signature: str
    severity: str = "CRITICAL"  # "CRITICAL" | "WARNING"

    def format_message(self) -> str:
        return (
            f"[{self.severity}] Contract Coherence Violation in '{self.file}' symbol '{self.symbol}': "
            f"Expected {self.expected_signature}, but found {self.actual_signature}."
        )


@dataclass
class TypeContract:
    """Represents a declared interface or data type contract."""
    name: str
    source_file: str
    fields: Dict[str, str] = field(default_factory=dict)  # field_name -> field_type
    is_enum: bool = False
    enum_values: List[str] = field(default_factory=list)


class CategoricalCoherenceChecker:
    """
    Extracts type contracts from ground-truth type files and validates
    that all implementation functions, hooks, and components preserve
    structural contract consistency.
    """

    INTERFACE_PATTERN = re.compile(
        r"(?:export\s+)?interface\s+([A-Za-z0-9_]+)(?:\s+extends\s+[^{]+)?\s*\{([^}]+)\}",
        re.DOTALL,
    )
    TYPE_ALIAS_PATTERN = re.compile(
        r"(?:export\s+)?type\s+([A-Za-z0-9_]+)\s*=\s*\{([^}]+)\}",
        re.DOTALL,
    )
    ENUM_PATTERN = re.compile(
        r"(?:export\s+)?enum\s+([A-Za-z0-9_]+)\s*\{([^}]+)\}",
        re.DOTALL,
    )
    PY_CLASS_PATTERN = re.compile(
        r"class\s+([A-Za-z0-9_]+)(?:\([^)]*\))?:\s*\n((?:\s+[^\n]+\n)+)",
        re.MULTILINE,
    )

    # Function signatures (standard, async, arrow functions)
    FUNCTION_PATTERN = re.compile(
        r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)",
        re.MULTILINE,
    )
    ARROW_PATTERN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>",
        re.MULTILINE,
    )
    REACT_FC_PATTERN = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+([A-Za-z0-9_]+)\s*:\s*(?:React\.)?(?:FC|FunctionComponent)<([^>]+)>\s*=\s*\(([^)]*)\)\s*=>",
        re.MULTILINE,
    )

    def extract_contracts(self, type_files: Dict[str, str]) -> Dict[str, TypeContract]:
        """
        Extract all declared interfaces, type aliases, and enums from contract files.
        """
        contracts: Dict[str, TypeContract] = {}

        for rel_path, content in type_files.items():
            ext = rel_path.rsplit(".", 1)[-1].lower() if "." in rel_path else ""

            if ext in ("ts", "tsx", "js", "jsx"):
                # 1. TypeScript Interfaces
                for match in self.INTERFACE_PATTERN.finditer(content):
                    name = match.group(1).strip()
                    body = match.group(2)
                    fields = self._parse_ts_body(body)
                    contracts[name] = TypeContract(name=name, source_file=rel_path, fields=fields)

                # 2. TypeScript Type Aliases
                for match in self.TYPE_ALIAS_PATTERN.finditer(content):
                    name = match.group(1).strip()
                    body = match.group(2)
                    fields = self._parse_ts_body(body)
                    if name not in contracts:
                        contracts[name] = TypeContract(name=name, source_file=rel_path, fields=fields)

                # 3. Enums
                for match in self.ENUM_PATTERN.finditer(content):
                    name = match.group(1).strip()
                    body = match.group(2)
                    enum_vals = [
                        v.split("=")[0].strip()
                        for v in body.split(",")
                        if v.strip() and not v.strip().startswith("//")
                    ]
                    contracts[name] = TypeContract(
                        name=name,
                        source_file=rel_path,
                        is_enum=True,
                        enum_values=enum_vals,
                    )

            elif ext == "py":
                # Python dataclasses / Pydantic models
                for match in self.PY_CLASS_PATTERN.finditer(content):
                    name = match.group(1).strip()
                    body = match.group(2)
                    fields = {}
                    for line in body.splitlines():
                        line = line.strip()
                        if ":" in line and not line.startswith("#") and not line.startswith("def "):
                            parts = line.split(":", 1)
                            fname = parts[0].strip()
                            ftype = parts[1].split("=")[0].strip()
                            if fname and not fname.startswith("_"):
                                fields[fname] = ftype
                    if fields:
                        contracts[name] = TypeContract(name=name, source_file=rel_path, fields=fields)

        return contracts

    def _parse_ts_body(self, body: str) -> Dict[str, str]:
        fields: Dict[str, str] = {}
        for line in body.splitlines():
            line = line.strip().rstrip(";").rstrip(",")
            if ":" in line and not line.startswith("//") and not line.startswith("/*"):
                parts = line.split(":", 1)
                field_name = parts[0].strip().rstrip("?").strip("'\"")
                field_type = parts[1].strip()
                if field_name and not field_name.startswith("["):
                    fields[field_name] = field_type
        return fields

    def check_coherence(
        self,
        contracts: Dict[str, TypeContract],
        implementation_files: Dict[str, str],
    ) -> List[ContractViolation]:
        """
        Scan implementation files and verify that parameters, destructuring, and types
        respect declared TypeContracts.
        """
        violations: List[ContractViolation] = []

        if not contracts:
            return violations

        # Regex for destructured parameters with explicit type annotation: ({ a, b }: MyType)
        destruct_typed_re = re.compile(
            r"\{\s*([^}]+?)\s*\}\s*:\s*([A-Za-z0-9_]+)",
        )

        for rel_path, content in implementation_files.items():
            if ".test." in rel_path or ".spec." in rel_path:
                continue

            # 1. Inspect function signatures
            for pattern in (self.FUNCTION_PATTERN, self.ARROW_PATTERN):
                for match in pattern.finditer(content):
                    fn_name = match.group(1)
                    params = match.group(2)

                    for d_match in destruct_typed_re.finditer(params):
                        fields_str = d_match.group(1)
                        type_name = d_match.group(2)

                        if type_name in contracts:
                            contract = contracts[type_name]
                            if contract.fields:
                                for raw_item in fields_str.split(","):
                                    item = raw_item.strip().split(":")[0].split("=")[0].strip()
                                    if item and not item.startswith("...") and item not in contract.fields:
                                        violations.append(
                                            ContractViolation(
                                                file=rel_path,
                                                symbol=fn_name,
                                                expected_signature=f"fields in '{type_name}' ({list(contract.fields.keys())})",
                                                actual_signature=f"destructured undeclared field '{item}' from '{type_name}'",
                                                severity="CRITICAL",
                                            )
                                        )

            # 2. Inspect React.FC<Props> definitions
            for match in self.REACT_FC_PATTERN.finditer(content):
                comp_name = match.group(1)
                type_name = match.group(2).strip()
                params = match.group(3)

                if type_name in contracts:
                    contract = contracts[type_name]
                    if contract.fields:
                        d_match = re.search(r"\{\s*([^}]+?)\s*\}", params)
                        if d_match:
                            fields_str = d_match.group(1)
                            for raw_item in fields_str.split(","):
                                item = raw_item.strip().split(":")[0].split("=")[0].strip()
                                if item and not item.startswith("...") and item not in contract.fields:
                                    violations.append(
                                        ContractViolation(
                                            file=rel_path,
                                            symbol=comp_name,
                                            expected_signature=f"props in '{type_name}' ({list(contract.fields.keys())})",
                                            actual_signature=f"component prop '{item}' not in contract '{type_name}'",
                                            severity="CRITICAL",
                                        )
                                    )

        return violations

    def compute_coherence_score(
        self,
        violations: List[ContractViolation],
        total_files_checked: int,
    ) -> float:
        """
        Compute a normalized categorical coherence score between 0.0 and 1.0.
        """
        if not total_files_checked:
            return 1.0
        critical_count = sum(1 for v in violations if v.severity == "CRITICAL")
        penalty = min(1.0, critical_count * 0.25)
        return max(0.0, 1.0 - penalty)
