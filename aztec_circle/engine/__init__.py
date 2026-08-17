"""
Engine modules for Aztec Decision Circle.
"""

from aztec_circle.engine.budget_manager import BudgetManager
from aztec_circle.engine.checkpoint import CheckpointStore
from aztec_circle.engine.consensus import ConsensusEngine
from aztec_circle.engine.state_machine import AztecOrchestrator
from aztec_circle.engine.scaffolder import (
    scaffold_project,
    find_project_root,
    ScaffoldResult,
    detect_uses_tailwind,
    detect_heavy_deps,
)
from aztec_circle.engine.project_runner import ProjectRunner, CommandResult, ServerProcess, PortInUseError
from aztec_circle.engine.build_fixer import BuildFixAgent, FixResult, TSError
from aztec_circle.engine.project_indexer import ProjectIndexer, ProjectIndex, FileIndex
from aztec_circle.engine.updater import AztecUpdater, UpdateCheckResult, UpdateExecutionResult
from aztec_circle.engine.plan_manager import PlanManager
from aztec_circle.engine.patch_agent import PatchAgent, PatchApplicator, FilePatch, PatchResult
from aztec_circle.engine.linking_engine import (
    LinkingEngine,
    DependencyGraph,
    FileNode,
    IntegrationManifest,
    load_project_aztec_config,
)
from aztec_circle.engine.integration_enforcer import enforce_mandatory_patches
from aztec_circle.engine.post_apply_verifier import PostApplyVerifier, VerificationResult

__all__ = [
    "BudgetManager",
    "CheckpointStore",
    "ConsensusEngine",
    "AztecOrchestrator",
    "PlanManager",
    "scaffold_project",
    "find_project_root",
    "ScaffoldResult",
    "detect_uses_tailwind",
    "detect_heavy_deps",
    "ProjectRunner",
    "CommandResult",
    "ServerProcess",
    "PortInUseError",
    "BuildFixAgent",
    "FixResult",
    "TSError",
    "ProjectIndexer",
    "ProjectIndex",
    "FileIndex",
    "PatchAgent",
    "PatchApplicator",
    "FilePatch",
    "PatchResult",
    "AztecUpdater",
    "UpdateCheckResult",
    "UpdateExecutionResult",
    "LinkingEngine",
    "DependencyGraph",
    "FileNode",
    "IntegrationManifest",
    "load_project_aztec_config",
    "enforce_mandatory_patches",
    "PostApplyVerifier",
    "VerificationResult",
]
