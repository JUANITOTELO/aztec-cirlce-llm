"""
Unit tests for ASTValidator (syntactic grammar validation with tree-sitter & fallbacks).
"""

import pytest
from aztec_circle.engine.ast_validator import ASTValidator


def test_ast_validator_valid_typescript():
    validator = ASTValidator()
    code = """
    import React, { useState } from 'react';

    export interface ButtonProps {
        label: string;
        onClick: () => void;
    }

    export const Button: React.FC<ButtonProps> = ({ label, onClick }) => {
        return <button onClick={onClick}>{label}</button>;
    };
    """
    res = validator.validate(code, "src/atoms/Button.tsx")
    assert res.is_valid
    assert len(res.errors) == 0


def test_ast_validator_invalid_typescript():
    validator = ASTValidator()
    # Unclosed JSX tag / unclosed brace syntax error
    bad_code = """
    export const Broken = () => {
        return <div><span>Unclosed;
    };
    """
    res = validator.validate(bad_code, "src/atoms/Broken.tsx")
    assert not res.is_valid
    assert len(res.errors) > 0


def test_ast_validator_valid_python():
    validator = ASTValidator()
    py_code = """
def calculate_tax(amount: float, rate: float = 0.08) -> float:
    return round(amount * rate, 2)
"""
    res = validator.validate(py_code, "backend/tax.py")
    assert res.is_valid


def test_ast_validator_invalid_python():
    validator = ASTValidator()
    bad_py = "def invalid_func(\n    return 42"
    res = validator.validate(bad_py, "backend/bad.py")
    assert not res.is_valid
    assert len(res.errors) > 0
