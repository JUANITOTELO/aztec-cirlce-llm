"""
Unit tests for output_schema.py (JSON schema validation & new_files key sanitizer).
"""

import pytest
from aztec_circle.engine.output_schema import (
    ELDER_AUDIT_SCHEMA,
    PEER_MODULAR_SCHEMA,
    sanitize_new_files_keys,
    validate_json_schema,
)


def test_sanitize_new_files_keys():
    raw_files = {
        "src/types/category.ts": "export interface Category { id: string }",
        "src/components/CategoryList.tsx": "export const CategoryList = () => null;",
        "category": "invalid string key",
        "payload": "invalid payload key",
    }
    valid_map, invalid_keys = sanitize_new_files_keys(raw_files)

    assert "src/types/category.ts" in valid_map
    assert "src/components/CategoryList.tsx" in valid_map
    assert len(invalid_keys) == 2
    assert "category" in invalid_keys
    assert "payload" in invalid_keys


def test_validate_peer_modular_schema():
    valid_payload = {
        "architecture_overview": "New Categories Module",
        "new_files": {
            "src/types/category.ts": "export interface Category {}",
        },
        "patches": [
            {
                "file": "src/App.tsx",
                "action": "replace",
                "start_line": 10,
                "end_line": 20,
                "replacement": "// new content",
                "concern": "Wire categories",
            }
        ],
        "commands": [
            {"command": "npm test", "stage": "post_patch"}
        ],
    }
    is_valid, errors = validate_json_schema(valid_payload, PEER_MODULAR_SCHEMA)
    assert is_valid
    assert len(errors) == 0


def test_validate_elder_audit_schema():
    valid_elder = {
        "status": "APPROVED",
        "weighted_score": 9.2,
        "audit_items": [
            {
                "criterion": "Holistic Linking & Integration Completeness",
                "weight": 0.25,
                "score": 9.5,
                "critique": "Well linked",
                "passed": True,
            }
        ],
        "critical_flaws": [],
    }
    is_valid, errors = validate_json_schema(valid_elder, ELDER_AUDIT_SCHEMA)
    assert is_valid
