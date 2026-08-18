import { LeanTacticState } from '../../types/lean';
import { GeometryParams } from '../../types/proofState';
import { computeProofHash } from '../../utils/cryptoHash';
import { BINOMIAL_TACTIC_EXPLANATIONS } from '../../constants/binomialPresets';

export function generateBinomialTactics(params: GeometryParams): LeanTacticState[] {
  const { a, b } = params;
  const a2 = a * a;
  const b2 = b * b;
  const ab2 = 2 * a * b;
  const total = (a + b) * (a + b);

  const tactics = [
    'intro a b ha hb',
    'have h_diag : (a + b)^2 = a^2 + b^2 + 2 * (a * b) := by geometric_dissection',
    'have h_rect : 2 * (a * b) = 4 * ((1 / 2 : ℝ) * a * b) := by ring_nf',
    'rw [h_rect] at h_diag',
    'have h_sum : a^2 + 4 * ((1 / 2 : ℝ) * a * b) + b^2 = a^2 + 2 * a * b + b^2 := by ring_nf',
    'ring_nf'
  ];

  return tactics.map((tactic, index) => {
    const hash = computeProofHash(`binomial:${a}:${b}:${index}:${tactic}`);
    return {
      stepIndex: index,
      tacticApplied: tactic,
      hypotheses: [
        { id: 'h1', name: 'ha', type: `a > 0 (a = ${a})` },
        { id: 'h2', name: 'hb', type: `b > 0 (b = ${b})` },
        ...(index >= 1 ? [{ id: 'h3', name: 'h_geom', type: `area((a+b)²) = ${total}` }] : []),
        ...(index >= 3 ? [{ id: 'h4', name: 'h_quads', type: `a²=${a2}, b²=${b2}, 2ab=${ab2}` }] : [])
      ],
      goals: index === 5 ? [] : [`⊢ (a + b)^2 = a^2 + 2*a*b + b^2`],
      status: index === 5 ? 'PROVEN' : 'IN_PROGRESS',
      merkleHash: hash,
      logicalClock: index + 1,
      explanation: BINOMIAL_TACTIC_EXPLANATIONS[index] || 'Verify binomial step'
    };
  });
}
