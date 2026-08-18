import { LeanTacticState } from '../types/lean';
import { GeometryParams, TheoremType } from '../types/proofState';
import { computeProofHash } from '../utils/cryptoHash';
import { TACTIC_EXPLANATIONS } from '../constants/leanPresets';
import { generateBinomialTactics } from './theorems/binomialTactics';
import { generateGouguTactics } from './theorems/gouguTactics';

export class LeanKernelSimulator {
  public static generateTactics(params: GeometryParams, theorem: TheoremType = 'pythagoras'): LeanTacticState[] {
    if (theorem === 'binomial') {
      return generateBinomialTactics(params);
    }
    if (theorem === 'gougu') {
      return generateGouguTactics(params);
    }
    const { a, b } = params;
    const c = params.c ?? Math.round(Math.hypot(a, b) * 1000) / 1000;
    const tactics = [
      'intro a b c h_pos h_outer',
      'have h_alg : (a + b)^2 = a^2 + 2 * a * b + b^2 := by ring',
      'have h_tri : 4 * ((1 / 2 : ℝ) * a * b) = 2 * a * b := by ring_nf',
      'rw [h_alg, h_tri] at h_outer',
      'have h_cancel : a^2 + b^2 = c^2 := by linear_combination h_outer',
      'exact h_cancel'
    ];

    return tactics.map((tactic, index) => {
      const hash = computeProofHash(`pythagoras:${a}:${b}:${c}:${index}:${tactic}`);
      return {
        stepIndex: index,
        tacticApplied: tactic,
        hypotheses: [
          { id: 'h1', name: 'h_pos', type: '0 < a ∧ 0 < b ∧ 0 < c' },
          ...(index < 3 ? [{ id: 'h2', name: 'h_outer', type: '(a + b)^2 = c^2 + 4 * ((1 / 2 : ℝ) * a * b)' }] : []),
          ...(index >= 1 ? [{ id: 'h3', name: 'h_alg', type: '(a + b)^2 = a^2 + 2 * a * b + b^2' }] : []),
          ...(index >= 2 ? [{ id: 'h4', name: 'h_tri', type: '4 * ((1 / 2 : ℝ) * a * b) = 2 * a * b' }] : []),
          ...(index >= 3 ? [{ id: 'h2_rw', name: 'h_outer', type: 'a^2 + 2 * a * b + b^2 = c^2 + 2 * a * b' }] : []),
          ...(index >= 4 ? [{ id: 'h5', name: 'h_cancel', type: 'a^2 + b^2 = c^2' }] : [])
        ],
        goals: index === 5 ? [] : ['⊢ a^2 + b^2 = c^2'],
        status: index === 5 ? 'PROVEN' : 'IN_PROGRESS',
        merkleHash: hash,
        logicalClock: index + 1,
        explanation: TACTIC_EXPLANATIONS[index] || 'Apply Lean 4 kernel tactic'
      };
    });
  }
}
