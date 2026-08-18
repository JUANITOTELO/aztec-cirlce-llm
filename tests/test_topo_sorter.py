"""
Unit tests for TopologicalSorter (Kahn's algorithm, cycle detection, layer violations).
"""

import pytest
from aztec_circle.engine.codegen_ir import FileRole
from aztec_circle.engine.topo_sorter import TopologicalSorter


def test_topo_sorter_linear_dag():
    sorter = TopologicalSorter()
    nodes = ["src/App.tsx", "src/hooks/useCart.ts", "src/types/cart.ts", "src/engine/pricing.ts"]
    edges = {
        "src/App.tsx": ["src/hooks/useCart.ts"],
        "src/hooks/useCart.ts": ["src/engine/pricing.ts", "src/types/cart.ts"],
        "src/engine/pricing.ts": ["src/types/cart.ts"],
        "src/types/cart.ts": [],
    }

    order, cycles = sorter.sort(nodes, edges)
    assert len(cycles) == 0

    # Dependencies must appear before consumers
    assert order.index("src/types/cart.ts") < order.index("src/engine/pricing.ts")
    assert order.index("src/engine/pricing.ts") < order.index("src/hooks/useCart.ts")
    assert order.index("src/hooks/useCart.ts") < order.index("src/App.tsx")


def test_topo_sorter_detects_cycle():
    sorter = TopologicalSorter()
    nodes = ["a.ts", "b.ts", "c.ts"]
    edges = {
        "a.ts": ["b.ts"],
        "b.ts": ["c.ts"],
        "c.ts": ["a.ts"],
    }

    order, cycles = sorter.sort(nodes, edges)
    assert len(cycles) > 0
    cycle_nodes = set(cycles[0])
    assert "a.ts" in cycle_nodes
    assert "b.ts" in cycle_nodes
    assert "c.ts" in cycle_nodes


def test_topo_sorter_layer_violations():
    sorter = TopologicalSorter()
    roles = {
        "src/engine/pricing.ts": FileRole.DOMAIN_ENGINE,
        "src/components/CartModal.tsx": FileRole.UI_COMPONENT,
        "src/types/cart.ts": FileRole.TYPE_CONTRACT,
    }
    # Illegal: domain engine importing UI component!
    illegal_edges = {
        "src/engine/pricing.ts": ["src/components/CartModal.tsx"],
        "src/components/CartModal.tsx": ["src/types/cart.ts"],
    }

    violations = sorter.check_layer_violations(roles, illegal_edges)
    assert len(violations) == 1
    assert "TOPOLOGICAL LAYER VIOLATION" in violations[0]
    assert "src/engine/pricing.ts" in violations[0]
