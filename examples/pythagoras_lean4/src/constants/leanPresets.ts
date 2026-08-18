export const LEAN_VERSION = 'v4.7.0';
export const LEAN_TOOLCHAIN = 'leanprover/lean4:v4.7.0';

export const DEFAULT_GEOMETRY = {
  a: 6,
  b: 8,
  c: 10
};

export const TACTIC_EXPLANATIONS = [
  'Initialize theorem context and right triangle hypotheses (a > 0, b > 0, c > 0).',
  'Formulate geometric dissection area identity: outer square (a + b)² equals c² + 4 * (ab/2).',
  'Expand algebraic square (a + b)² into a² + 2ab + b² using the `ring` tactic.',
  'Simplify right triangle 4-fold summation: 4 * (1/2 * ab) = 2ab.',
  'Substitute expanded identities into the geometric area equality equation.',
  'Apply linear arithmetic (`linarith`) to cancel 2ab from both sides, yielding a² + b² = c².'
];