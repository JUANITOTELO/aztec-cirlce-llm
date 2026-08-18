"""
Topological Sorter — Graph ordering and cycle detection for Aztec code generation.

Implements Kahn's algorithm and DFS cycle detection over module dependency graphs
to ensure mathematically correct synthesis sequences (foundations before consumers).
"""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

from aztec_circle.engine.codegen_ir import FileRole

# Layer hierarchy for architectural directionality check
ROLE_LAYER_MAP: Dict[FileRole, int] = {
    FileRole.CONFIG: 0,
    FileRole.TYPE_CONTRACT: 1,
    FileRole.MIGRATION: 2,
    FileRole.BACKEND: 2,
    FileRole.DOMAIN_ENGINE: 2,
    FileRole.STATE_STORE: 2,
    FileRole.HOOK: 3,
    FileRole.UI_ATOM: 4,
    FileRole.UI_COMPONENT: 5,
    FileRole.COORDINATOR: 6,
    FileRole.TEST: 7,
    FileRole.UNKNOWN: 5,
}


class TopologicalSorter:
    """
    Kahn's algorithm BFS topological sort over a directed import graph.

    Categorical correctness guarantee:
    - Each file is an object in the category of source files.
    - Each dependency is a directed morphism (consumer -> dependency).
    - A valid total topological ordering exists iff the graph is a Directed Acyclic Graph (DAG).
    """

    def sort(
        self,
        nodes: List[str],
        edges: Dict[str, List[str]],  # node -> list of dependencies that node depends on
    ) -> Tuple[List[str], List[List[str]]]:
        """
        Produce a topological sort where dependencies appear BEFORE the nodes that depend on them.

        Args:
            nodes: List of all node identifiers (e.g. relative file paths).
            edges: Dict mapping each node to the list of nodes it depends on.

        Returns:
            (sorted_order, cycles)
            sorted_order: Dependencies first, followed by consumers.
            cycles: List of detected cyclic dependency paths, if any.
        """
        all_nodes = list(dict.fromkeys(nodes))
        # in_degree counts how many dependencies a node still has unresolved in BFS
        in_degree: Dict[str, int] = {n: 0 for n in all_nodes}
        # adjacency maps dependency -> list of dependents (consumers) waiting on it
        adjacency: Dict[str, List[str]] = defaultdict(list)

        for node in all_nodes:
            deps = edges.get(node, [])
            for dep in deps:
                if dep in in_degree and dep != node:
                    adjacency[dep].append(node)
                    in_degree[node] += 1

        # Nodes with in_degree == 0 have no local dependencies in the set
        queue = deque([n for n in all_nodes if in_degree[n] == 0])
        order: List[str] = []

        while queue:
            node = queue.popleft()
            order.append(node)
            for dependent in adjacency[node]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(order) < len(all_nodes):
            remaining = {n for n in all_nodes if n not in set(order)}
            cycles = self._detect_cycles(remaining, edges)
            # Append remaining in stable order for graceful degradation
            for n in all_nodes:
                if n not in order:
                    order.append(n)
            return order, cycles

        return order, []

    def _detect_cycles(
        self,
        remaining_nodes: Set[str],
        edges: Dict[str, List[str]],
    ) -> List[List[str]]:
        """
        DFS graph cycle detection using three-color state:
        0: unvisited (WHITE), 1: visiting (GRAY), 2: visited (BLACK).
        """
        color: Dict[str, int] = {n: 0 for n in remaining_nodes}
        cycles: List[List[str]] = []
        path: List[str] = []

        def dfs(node: str) -> None:
            color[node] = 1
            path.append(node)
            for dep in edges.get(node, []):
                if dep not in remaining_nodes:
                    continue
                if color.get(dep, 0) == 1:
                    # Found back-edge to an ancestor on current path
                    try:
                        idx = path.index(dep)
                        cycle = path[idx:] + [dep]
                        cycles.append(cycle)
                    except ValueError:
                        cycles.append([node, dep])
                elif color.get(dep, 0) == 0:
                    dfs(dep)
            path.pop()
            color[node] = 2

        for n in sorted(remaining_nodes):
            if color.get(n, 0) == 0:
                dfs(n)

        return cycles

    def check_layer_violations(
        self,
        node_roles: Dict[str, FileRole],
        edges: Dict[str, List[str]],
    ) -> List[str]:
        """
        Validates topological layer discipline:
        A lower-layer file (e.g. domain engine) must NEVER import from a higher-layer file (e.g. UI component or coordinator).
        """
        violations: List[str] = []
        for consumer, deps in edges.items():
            consumer_role = node_roles.get(consumer, FileRole.UNKNOWN)
            consumer_layer = ROLE_LAYER_MAP.get(consumer_role, 5)

            for dep in deps:
                dep_role = node_roles.get(dep, FileRole.UNKNOWN)
                dep_layer = ROLE_LAYER_MAP.get(dep_role, 5)

                # Violations: strict lower-layer depending on higher-layer
                # Exceptions: tests (layer 7) can depend on anything
                if consumer_layer < dep_layer and consumer_role != FileRole.TEST:
                    violations.append(
                        f"TOPOLOGICAL LAYER VIOLATION: '{consumer}' (Layer {consumer_layer}: {consumer_role.value}) "
                        f"imports from higher layer '{dep}' (Layer {dep_layer}: {dep_role.value})."
                    )

        return violations
