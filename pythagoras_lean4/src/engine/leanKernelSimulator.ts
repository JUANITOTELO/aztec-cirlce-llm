import { LeanTacticState, ProofStatus } from '../types/lean';
import { GeometryParams } from '../types/proofState';
import { computeProofHash, computeMerkleRoot } from '../utils/cryptoHash';
import { TACTIC_EXPLANATIONS } from '../constants/leanPresets';

export class LeanKernelSimulator {
  private logicalClock = 0;
  private stateHistory: LeanTacticState[] = [];

  public generateTacticSequence(params: GeometryParams): readonly LeanTacticState[] {
    this.logicalClock++;
    const { a, b, c } = params;
    const states: LeanTacticState[] = [];

    const steps = [
      {
        tactic: 'intro (t : RightTriangle)',
        hyps: [
          { id: 'h1', name: 't.a', type: 'ℝ', value: `${a}`, isImplicit: false },
          { id: 'h2', name: 't.b', type: 'ℝ', value: `${b}`, isImplicit: false },
          { id: 'h3', name: 't.c', type: 'ℝ', value: `${c}`, isImplicit: false },
          { id: 'h4', name: 't.ha', type: `0 < ${a}`, isImplicit: true },
          { id: 'h5', name: 't.hb', type: `0 < ${b}`, isImplicit: true }
        ],
        goals: [`⊢ (t.a + t.b)^2 = t.c^2 + 4 * (1/2 * (t.a * t.b)) → t.a^2 + t.b^2 = t.c^2`],
        status: 'IN_PROGRESS' as ProofStatus
      },
      {
        tactic: 'intro h_area',
        hyps: [
          { id: 'h1', name: 't.a', type: 'ℝ', value: `${a}` },
          { id: 'h2', name: 't.b', type: 'ℝ', value: `${b}` },
          { id: 'h3', name: 't.c', type: 'ℝ', value: `${c}` },
          { id: 'h_area', name: 'h_area', type: `(${a} + ${b})^2 = ${c}^2 + 4 * (1/2 * (${a} * ${b}))` }
        ],
        goals: [`⊢ ${a}^2 + ${b}^2 = ${c}^2`],
        status: 'IN_PROGRESS' as ProofStatus
      },
      {
        tactic: 'have h_expand : (t.a + t.b)^2 = t.a^2 + 2 * t.a * t.b + t.b^2 := by ring',
        hyps: [
          { id: 'h_area', name: 'h_area', type: `(${a} + ${b})^2 = ${c}^2 + 2 * ${a} * ${b}` },
          { id: 'h_expand', name: 'h_expand', type: `(${a} + ${b})^2 = ${a}^2 + 2*${a}*${b} + ${b}^2` }
        ],
        goals: [`⊢ ${a}^2 + ${b}^2 = ${c}^2`],
        status: 'IN_PROGRESS' as ProofStatus
      },
      {
        tactic: 'have h_triangles : 4 * (1 / 2 * (t.a * t.b)) = 2 * t.a * t.b := by ring',
        hyps: [
          { id: 'h_expand', name: 'h_expand', type: `(${a} + ${b})^2 = ${a}^2 + 2*${a}*${b} + ${b}^2` },
          { id: 'h_triangles', name: 'h_triangles', type: `4 * (1/2 * (${a} * ${b})) = 2 * ${a} * ${b}` }
        ],
        goals: [`⊢ ${a}^2 + ${b}^2 = ${c}^2`],
        status: 'IN_PROGRESS' as ProofStatus
      },
      {
        tactic: 'rw [h_expand, h_triangles] at h_area',
        hyps: [
          { id: 'h_area_rw', name: 'h_area', type: `${a}^2 + 2*${a}*${b} + ${b}^2 = ${c}^2 + 2*${a}*${b}` }
        ],
        goals: [`⊢ ${a}^2 + ${b}^2 = ${c}^2`],
        status: 'IN_PROGRESS' as ProofStatus
      },
      {
        tactic: 'linarith',
        hyps: [
          { id: 'qed', name: 'proof_term', type: `Eq.refl (${a * a + b * b} = ${c * c})` }
        ],
        goals: ['goals accomplished 🎉'],
        status: 'PROVEN' as ProofStatus
      }
    ];

    const rawHashes: string[] = [];
    steps.forEach((s, idx) => {
      const stepHash = computeProofHash(`${this.logicalClock}:${idx}:${s.tactic}:${params.a}:${params.b}`);
      rawHashes.push(stepHash);
      const merkle = computeMerkleRoot(rawHashes);

      states.push({
        stepIndex: idx,
        tacticApplied: s.tactic,
        hypotheses: s.hyps,
        goals: s.goals,
        status: s.status,
        merkleHash: merkle,
        logicalClock: this.logicalClock,
        explanation: TACTIC_EXPLANATIONS[idx] || 'Tactic transformation'
      });
    });

    this.stateHistory = states;
    return states;
  }

  public verifyProofCertificate(states: readonly LeanTacticState[]): boolean {
    if (!states || states.length === 0) return false;
    const lastStep = states[states.length - 1];
    return lastStep.status === 'PROVEN' && lastStep.goals[0]?.includes('accomplished');
  }
}