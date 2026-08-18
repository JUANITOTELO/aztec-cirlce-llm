"""
Output Schemas — Formal JSON Schema definitions and validator for LLM outputs.

Enforces schema contracts on generated code, patches, commands, and audit verdicts
to prevent structurally malformed LLM responses from propagating through the pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import jsonschema


# Schema for full project scaffolding peer output
PEER_SCAFFOLD_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "architecture_overview": {"type": "string"},
        "implementation_code": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "mitigations_applied": {
            "type": "array",
            "items": {"type": "string"},
        },
        "assumptions_made": {
            "type": "array",
            "items": {"type": "string"},
        },
        "setup_commands": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["architecture_overview", "implementation_code"],
}


# Schema for modular consensus peer output (feature/module synthesis)
PEER_MODULAR_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "architecture_overview": {"type": "string"},
        "new_files": {
            "type": "object",
            "additionalProperties": {"type": "string"},
        },
        "patches": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file": {"type": "string"},
                    "action": {
                        "type": "string",
                        "enum": ["replace", "insert_before", "insert_after", "create", "delete"],
                    },
                    "start_line": {"type": ["integer", "null"]},
                    "end_line": {"type": ["integer", "null"]},
                    "replacement": {"type": ["string", "null"]},
                    "concern": {"type": "string"},
                },
                "required": ["file", "action"],
            },
        },
        "commands": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "description": {"type": "string"},
                    "stage": {"type": "string", "enum": ["pre_patch", "post_patch"]},
                    "cwd": {"type": ["string", "null"]},
                },
                "required": ["command"],
            },
        },
        "mitigations_applied": {
            "type": "array",
            "items": {"type": "string"},
        },
        "assumptions_made": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["architecture_overview"],
}


# Schema for Elder audit verdict output
ELDER_AUDIT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["APPROVED", "REJECTED", "HALT_OVERRIDE"],
        },
        "weighted_score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 10.0,
        },
        "audit_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string"},
                    "weight": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "score": {"type": "number", "minimum": 0.0, "maximum": 10.0},
                    "critique": {"type": "string"},
                    "passed": {"type": "boolean"},
                },
                "required": ["criterion", "score", "passed"],
            },
        },
        "critical_flaws": {
            "type": "array",
            "items": {"type": "string"},
        },
        "reworking_instructions": {"type": ["string", "null"]},
    },
    "required": ["status"],
}


def validate_json_schema(payload: Any, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a parsed Python dictionary against a JSON Schema.

    Returns:
        (is_valid, error_messages)
    """
    if not isinstance(payload, dict):
        return False, [f"Expected JSON object (dict), got {type(payload).__name__}"]

    validator = jsonschema.Draft202012Validator(schema)
    errors: List[str] = []

    for err in validator.iter_errors(payload):
        path = ".".join(str(p) for p in err.path)
        loc = f" at '{path}'" if path else ""
        errors.append(f"Schema violation{loc}: {err.message}")

    return len(errors) == 0, errors


def sanitize_new_files_keys(new_files: Dict[str, Any]) -> Tuple[Dict[str, str], List[str]]:
    """
    Validate that every key in new_files is a relative file path containing a slash
    and a recognized extension. Drops or flags bare-word keys like 'category', 'payload'.
    """
    valid_map: Dict[str, str] = {}
    invalid_keys: List[str] = []

    for k, v in new_files.items():
        k_clean = str(k).strip().lstrip("/\\").replace("\\", "/")
        has_slash = "/" in k_clean
        has_ext = "." in k_clean.rsplit("/", 1)[-1]

        if has_slash and has_ext:
            valid_map[k_clean] = str(v) if v is not None else ""
        else:
            invalid_keys.append(str(k))

    return valid_map, invalid_keys
