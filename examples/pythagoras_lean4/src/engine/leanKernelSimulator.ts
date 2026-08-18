import { LeanTacticState } from '../types/lean';
import { GeometryParams, TheoremType } from '../types/proofState';
import { computeProofHash } from '../utils/cryptoHash';
import { TACTIC_EXPLANATIONS } from '../constants/leanPresets';
import { generateBinomialTactics } from './theorems/binomialTactics';

export class LeanKernelSimulator {
  public static generateTactics(params: GeometryParams, theorem: TheoremType = 'pythagoras'): LeanTacticState[] {
    if (theorem === 'binomial') {
      return generateBinomialTactics(params);
    }

    const { a, b, c = 5 } = params;
    const tactics = [
      'intro a b c h_pos h_right',
      'have h_area : (a + b)^2 = c^2 + 4 * ((1 / 2 : ℝ) * a * b) := by geometric_dissection',
      'have h_alg : (a + b)^2 = a^2 + 2 * a * b + b^2 := by ring',
      'have h_tri : 4 * ((1 / 2 : ℝ) * a * b) = 2 * a * b := by ring_nf',
      'rw [h_alg, h_tri] at h_area',
      'linarith [h_area]'
    ];

    return tactics.map((tactic, index) => {
      const hash = computeProofHash(`pythagoras:${a}:${b}:${c}:${index}:${tactic}`);
      return {
        stepIndex: index,
        tacticApplied: tactic,
        hypotheses: [
          { id: 'h1', name: 'h_pos', type: `a > 0 ∧ b > 0 ∧ c > 0` },
          { id: 'h2', name: 'h_right', type: `RightTriangle a b c (a=${a}, b=${b}, c=${c})` },
          ...(index >= 1 ? [{ id: 'h3', name: 'h_geom', type: `area((a+b)²) = c² + 4*(ab/2)` }] : []),
          ...(index >= 4 ? [{ id: 'h4', name: 'h_algebra', type: `a² + 2ab + b² = c² + 2ab` }] : [])
        ],
        goals: index === 5 ? [] : [`⊢ a^2 + b^2 = c^2`],
        status: index === 5 ? 'PROVEN' : 'IN_PROGRESS',
        merkleHash: hash,
        logicalClock: index + 1,
        explanation: TACTIC_EXPLANATIONS[index] || 'Apply Lean 4 kernel tactic'
      };
    });
  }
}
