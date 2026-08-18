"""
Unit tests for IRBuilder (converting raw synthesis output to formal CodegenIR).
"""

import pytest
from aztec_circle.engine.codegen_ir import FileRole
from aztec_circle.engine.ir_builder import IRBuilder


def test_ir_builder_full_pipeline():
    builder = IRBuilder()
    new_files = {
        "src/types/inventory.ts": "export interface InventoryItem { id: string; sku: string; stock: number; }",
        "src/engine/inventoryMath.ts": (
            "import { InventoryItem } from '../types/inventory';\n"
            "export function isLowStock(item: InventoryItem): boolean { return item.stock < 5; }"
        ),
        "src/components/InventoryTable.tsx": (
            "import { InventoryItem } from '../types/inventory';\n"
            "export const InventoryTable = ({ item }: { item: InventoryItem }) => null;"
        ),
    }
    patches = [
        {
            "file": "src/App.tsx",
            "action": "replace",
            "start_line": 5,
            "end_line": 15,
            "replacement": "import { InventoryTable } from './components/InventoryTable';",
            "concern": "Wire table",
        }
    ]

    ir = builder.build(
        goal="Add inventory tracking",
        architecture_overview="Inventory tracking module with types, math, and UI",
        new_files=new_files,
        patches=patches,
    )

    assert ir.is_valid
    assert len(ir.files) == 3
    assert len(ir.patches) == 1
    assert ir.coherence_score == 1.0
    assert len(ir.cycle_errors) == 0

    # Verify classification
    assert ir.files["src/types/inventory.ts"].role == FileRole.TYPE_CONTRACT
    assert ir.files["src/engine/inventoryMath.ts"].role == FileRole.DOMAIN_ENGINE
    assert ir.files["src/components/InventoryTable.tsx"].role == FileRole.UI_COMPONENT


def test_ir_builder_flags_cycles():
    builder = IRBuilder()
    new_files = {
        "src/engine/a.ts": "import './b'; export const a = 1;",
        "src/engine/b.ts": "import './a'; export const b = 2;",
    }
    ir = builder.build(
        goal="Test cycle",
        architecture_overview="Circular files",
        new_files=new_files,
    )
    assert len(ir.cycle_errors) > 0
