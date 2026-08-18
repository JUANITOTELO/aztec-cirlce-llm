import { LeanTacticState } from '../../types/lean';
import { GeometryParams } from '../../types/proofState';
import { computeProofHash } from '../../utils/cryptoHash';
import { BINOMIAL_TACTIC_EXPLANATIONS } from '../../constants/binomialPresets';

export function generateBinomialTactics(params: GeometryParams): LeanTacticState[] {
  const { a, b } = params;

  const tactics = [
    'intro a b ha hb',
    'have h_grid : (a + b)^2 = a^2 + a * b + b * a + b^2 := by ring',
    'have h_comm : b * a = a * b := mul_comm b a',
    'rw [h_comm] at h_grid',
    'have h_sum : (a + b)^2 = a^2 + 2 * (a * b) + b^2 := by linear_combination h_grid',
    'ring_nf'
  ];

  return tactics.map((tactic, index) => {
    const hash = computeProofHash(`binomial:${a}:${b}:${index}:${tactic}`);
    return {
      stepIndex: index,
      tacticApplied: tactic,
      hypotheses: [
        { id: 'h1', name: 'ha', type: '0 < a' },
        { id: 'h2', name: 'hb', type: '0 < b' },
        ...(index >= 1 && index < 4 ? [{ id: 'h3', name: 'h_grid', type: '(a + b)^2 = a^2 + a * b + b * a + b^2' }] : []),
        ...(index >= 2 ? [{ id: 'h4', name: 'h_comm', type: 'b * a = a * b' }] : []),
        ...(index >= 4 ? [{ id: 'h3_rw', name: 'h_grid', type: '(a + b)^2 = a^2 + a * b + a * b + b^2' }] : []),
        ...(index >= 4 ? [{ id: 'h5', name: 'h_sum', type: '(a + b)^2 = a^2 + 2 * (a * b) + b^2' }] : [])
      ],
      goals: index === 5 ? [] : ['⊢ (a + b)^2 = a^2 + 2 * a * b + b^2'],
      status: index === 5 ? 'PROVEN' : 'IN_PROGRESS',
      merkleHash: hash,
      logicalClock: index + 1,
      explanation: BINOMIAL_TACTIC_EXPLANATIONS[index] || 'Verify Euclid II.4 binomial step'
    };
  });
}
