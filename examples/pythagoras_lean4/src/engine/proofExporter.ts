import { LeanProjectExport } from '../types/lean';
import { GeometryParams, TheoremType } from '../types/proofState';
import { LEAN_VERSION, LEAN_TOOLCHAIN } from '../constants/leanPresets';
import { computeProofHash } from '../utils/cryptoHash';

export function generateLeanProject(params: GeometryParams, theorem: TheoremType = 'pythagoras'): LeanProjectExport {
  const isBinomial = theorem === 'binomial';
  const leanSource = isBinomial
    ? `import Mathlib.Data.Real.Basic\nimport Mathlib.Tactic.Ring\nimport Mathlib.Tactic.LinearCombination\n\ntheorem pythagorean_dissection (a b c : ℝ)\n    (h_area : (a + b)^2 = c^2 + 4 * ((1 / 2 : ℝ) * a * b)) :\n    a^2 + b^2 = c^2 := by\n  linear_combination h_area`
    : `import Mathlib.Data.Real.Basic\nimport Mathlib.Tactic.Ring\n\ntheorem binomial_square_dissection (a b : ℝ) :\n    (a + b)^2 = a^2 + 2 * a * b + b^2 := by\n  ring`;
  const lakefile = `import Lake\nopen Lake DSL\n\npackage «dissection_proof» { }\nlean_lib «Dissection» { }\nrequire mathlib from git "https://github.com/leanprover-community/mathlib4" @ "${LEAN_VERSION}"`;
  const verificationHash = computeProofHash(`${leanSource}:${params.a}:${params.b}`);

  return {
    lakefile,
    leanSource,
    toolchain: LEAN_TOOLCHAIN,
    verificationHash,
    timestamp: new Date().toISOString()
  };
}
