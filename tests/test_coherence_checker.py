"""
Unit tests for CategoricalCoherenceChecker (type contract extraction & functor checking).
"""

import pytest
from aztec_circle.engine.coherence_checker import CategoricalCoherenceChecker


def test_extract_contracts_typescript():
    checker = CategoricalCoherenceChecker()
    types_content = """
    export interface UserProfile {
        id: string;
        username: string;
        email: string;
        isActive?: boolean;
    }

    export type AuthToken = {
        token: string;
        expiresAt: number;
    };

    export enum UserRole {
        ADMIN = 'ADMIN',
        USER = 'USER',
    }
    """
    contracts = checker.extract_contracts({"src/types/user.ts": types_content})

    assert "UserProfile" in contracts
    assert "id" in contracts["UserProfile"].fields
    assert "username" in contracts["UserProfile"].fields
    assert "email" in contracts["UserProfile"].fields
    assert "isActive" in contracts["UserProfile"].fields

    assert "AuthToken" in contracts
    assert "token" in contracts["AuthToken"].fields

    assert "UserRole" in contracts
    assert contracts["UserRole"].is_enum


def test_coherence_checker_detects_mismatched_destructuring():
    checker = CategoricalCoherenceChecker()
    types_content = """
    export interface Product {
        id: string;
        title: string;
        price: number;
    }
    """
    contracts = checker.extract_contracts({"src/types/product.ts": types_content})

    # Valid consumer
    valid_impl = """
    export function renderProduct({ id, title, price }: Product) {
        return `${title}: $${price}`;
    }
    """
    violations_clean = checker.check_coherence(contracts, {"src/components/ProductCard.tsx": valid_impl})
    assert len(violations_clean) == 0

    # Invalid consumer: using 'name' and 'cost' instead of 'title' and 'price'
    invalid_impl = """
    export function renderProduct({ id, name, cost }: Product) {
        return `${name}: $${cost}`;
    }
    """
    violations_bad = checker.check_coherence(contracts, {"src/components/ProductCard.tsx": invalid_impl})
    assert len(violations_bad) >= 2
    actual_sigs = [v.actual_signature for v in violations_bad]
    assert any("name" in s for s in actual_sigs)
    assert any("cost" in s for s in actual_sigs)


def test_coherence_checker_react_fc():
    checker = CategoricalCoherenceChecker()
    types_content = """
    export interface ModalProps {
        isOpen: boolean;
        onClose: () => void;
    }
    """
    contracts = checker.extract_contracts({"src/types/ui.ts": types_content})

    # FC with undeclared prop 'autoFocus'
    comp_content = """
    export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, autoFocus }) => {
        return <div>Modal</div>;
    };
    """
    violations = checker.check_coherence(contracts, {"src/atoms/Modal.tsx": comp_content})
    assert len(violations) == 1
    assert "autoFocus" in violations[0].actual_signature
