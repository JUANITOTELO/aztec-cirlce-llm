import { LeanProjectExport } from '../types/lean';
import { GeometryParams, TheoremType } from '../types/proofState';
import { LEAN_VERSION, LEAN_TOOLCHAIN } from '../constants/leanPresets';
import { computeProofHash } from '../utils/cryptoHash';

export function generateLeanProject(params: GeometryParams, theorem: TheoremType = 'pythagoras'): LeanProjectExport {
  let leanSource: string;
  let libName = 'Pythagoras';

  if (theorem === 'binomial') {
    libName = 'Binomial';
    leanSource = `import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
import Mathlib.Tactic.LinearCombination

/-- Geometric Binomial Square Dissection (Yang Hui / Euclid II.4) -/
theorem binomial_square_dissection (a b : ℝ) (ha : 0 < a) (hb : 0 < b) :
    (a + b)^2 = a^2 + 2 * a * b + b^2 := by
  have h_grid : (a + b)^2 = a^2 + a * b + b * a + b^2 := by ring
  have h_comm : b * a = a * b := mul_comm b a
  rw [h_comm] at h_grid
  have h_sum : (a + b)^2 = a^2 + 2 * (a * b) + b^2 := by linear_combination h_grid
  ring_nf`;
  } else if (theorem === 'gougu') {
    libName = 'Gougu';
    leanSource = `import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
import Mathlib.Tactic.LinearCombination

/-- Zhao Shuang's Gougu Theorem (Xian Tu Dissection / 勾股弦图) -/
theorem gougu_xiantu_dissection (gou gu xian : ℝ) (h_pos : 0 < gou ∧ 0 < gu ∧ 0 < xian)
    (h_xiantu : xian^2 = 4 * ((1 / 2 : ℝ) * gou * gu) + (gu - gou)^2) :
    gou^2 + gu^2 = xian^2 := by
  have h_huang_fang : (gu - gou)^2 = gu^2 - 2 * gu * gou + gou^2 := by ring
  have h_zhu_shi : 4 * ((1 / 2 : ℝ) * gou * gu) = 2 * gou * gu := by ring_nf
  rw [h_huang_fang, h_zhu_shi] at h_xiantu
  have h_cancel : gou^2 + gu^2 = xian^2 := by linear_combination -h_xiantu
  exact h_cancel`;
  } else {
    libName = 'Pythagoras';
    leanSource = `import Mathlib.Data.Real.Basic
import Mathlib.Tactic.Ring
import Mathlib.Tactic.LinearCombination

/-- Pythagorean Theorem (Square Dissection via (a + b)² = c² + 4 * (ab/2)) -/
theorem pythagorean_dissection (a b c : ℝ) (h_pos : 0 < a ∧ 0 < b ∧ 0 < c)
    (h_outer : (a + b)^2 = c^2 + 4 * ((1 / 2 : ℝ) * a * b)) :
    a^2 + b^2 = c^2 := by
  have h_alg : (a + b)^2 = a^2 + 2 * a * b + b^2 := by ring
  have h_tri : 4 * ((1 / 2 : ℝ) * a * b) = 2 * a * b := by ring_nf
  rw [h_alg, h_tri] at h_outer
  have h_cancel : a^2 + b^2 = c^2 := by linear_combination h_outer
  exact h_cancel`;
  }

  const lakefile = `import Lake\nopen Lake DSL\n\npackage «dissection_proof» { }\nlean_lib «${libName}» { }\nrequire mathlib from git "https://github.com/leanprover-community/mathlib4" @ "${LEAN_VERSION}"`;
  const verificationHash = computeProofHash(`${leanSource}:${params.a}:${params.b}`);
  return {
    lakefile,
    leanSource,
    toolchain: LEAN_TOOLCHAIN,
    verificationHash,
    timestamp: new Date().toISOString()
  };
}
