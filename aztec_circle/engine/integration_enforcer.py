"""
IntegrationPatchEnforcer — Verifies that generated patches cover all mandatory integration targets.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from aztec_circle.domain.models import ModularPatchItem
from aztec_circle.engine.linking_engine import IntegrationManifest


def enforce_mandatory_patches(
    manifest: IntegrationManifest,
    new_files: Dict[str, Any],
    patches: List[ModularPatchItem],
) -> List[str]:
    """
    Returns a list of critical flaws for any mandatory integration target
    that has no corresponding patch or new file representation.
    """
    addressed: Set[str] = set()

    for p in patches:
        if p.file:
            addressed.add(p.file.lstrip("/\\").replace("\\", "/").lower())

    for rel in new_files.keys():
        if isinstance(rel, str):
            addressed.add(rel.lstrip("/\\").replace("\\", "/").lower())

    flaws: List[str] = []
    for target in manifest.mandatory_patch_targets:
        clean_target = target.lstrip("/\\").replace("\\", "/").lower()
        role = manifest.entry_points.get(target, "coordinator")

        if clean_target not in addressed:
            flaws.append(
                f"MISSING MANDATORY INTEGRATION PATCH: '{target}' (role: {role}) "
                f"must be updated/patched to wire the new module. "
                f"The generated output contains no patch or new file entry for this coordinator."
            )

    return flaws
