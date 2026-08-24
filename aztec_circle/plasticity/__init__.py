"""
Neuroplasticity subsystem for the Aztec Decision Circle.

The circle is no longer a fixed-topology debate pipeline: like a brain, it
rewires itself across runs. Four cooperating mechanisms:

1. SynapticWeightAdapter  — soft-Hebbian adaptation of Elder council weights
                            based on observed auditor reliability.
2. HomeostaticThresholds  — self-tuning approval threshold / flaw penalty that
                            drift toward the quality/efficiency equilibrium.
3. DynamicModelRouter     — complexity-aware model routing with stress
                            escalation and budget-pressure degradation.
4. ExperienceMemory       — persistent SQLite record of runs, flaw categories,
                            and persona efficiency; distilled into
                            "institutional memory" injected into Peer drafting.

All state is bounded (weights clamped + normalized, thresholds floored/
ceilinged) so the system can never oscillate into degeneracy: plasticity
without stability is noise, stability without plasticity is rigidity.
"""

from aztec_circle.plasticity.engine import PlasticityEngine

__all__ = ["PlasticityEngine"]
