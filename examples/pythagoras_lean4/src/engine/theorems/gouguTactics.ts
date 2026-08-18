import { LeanTacticState } from '../../types/lean';
import { GeometryParams } from '../../types/proofState';
import { computeProofHash } from '../../utils/cryptoHash';
import { GOUGU_TACTIC_EXPLANATIONS } from '../../constants/gouguPresets';

export function generateGouguTactics(params: GeometryParams): LeanTacticState[] {
  const gou = Math.min(params.a, params.b);
  const gu = Math.max(params.a, params.b);
  const xian = params.c ?? Math.round(Math.hypot(gou, gu) * 1000) / 1000;

  const tactics = [
    'intro gou gu xian h_pos h_xiantu',
    'have h_huang_fang : (gu - gou)^2 = gu^2 - 2 * gu * gou + gou^2 := by ring',
    'have h_zhu_shi : 4 * ((1 / 2 : ℝ) * gou * gu) = 2 * gou * gu := by ring_nf',
    'rw [h_huang_fang, h_zhu_shi] at h_xiantu',
    'have h_cancel : gou^2 + gu^2 = xian^2 := by linear_combination -h_xiantu',
    'exact h_cancel'
  ];

  return tactics.map((tactic, index) => {
    const hash = computeProofHash(`gougu:${gou}:${gu}:${xian}:${index}:${tactic}`);
    return {
      stepIndex: index,
      tacticApplied: tactic,
      hypotheses: [
        { id: 'h1', name: 'h_pos', type: '0 < gou ∧ 0 < gu ∧ 0 < xian' },
        ...(index < 3 ? [{ id: 'h2', name: 'h_xiantu', type: 'xian^2 = 4 * ((1 / 2 : ℝ) * gou * gu) + (gu - gou)^2' }] : []),
        ...(index >= 1 ? [{ id: 'h3', name: 'h_huang_fang', type: '(gu - gou)^2 = gu^2 - 2 * gu * gou + gou^2' }] : []),
        ...(index >= 2 ? [{ id: 'h4', name: 'h_zhu_shi', type: '4 * ((1 / 2 : ℝ) * gou * gu) = 2 * gou * gu' }] : []),
        ...(index >= 3 ? [{ id: 'h2_rw', name: 'h_xiantu', type: 'xian^2 = 2 * gou * gu + (gu^2 - 2 * gu * gou + gou^2)' }] : []),
        ...(index >= 4 ? [{ id: 'h5', name: 'h_cancel', type: 'gou^2 + gu^2 = xian^2' }] : [])
      ],
      goals: index === 5 ? [] : ['⊢ gou^2 + gu^2 = xian^2'],
      status: index === 5 ? 'PROVEN' : 'IN_PROGRESS',
      merkleHash: hash,
      logicalClock: index + 1,
      explanation: GOUGU_TACTIC_EXPLANATIONS[index] || 'Apply Gougu Xian Tu step'
    };
  });
}
