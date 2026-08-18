export const LEAN_VERSION = 'v4.7.0';
export const LEAN_TOOLCHAIN = 'leanprover/lean4:v4.7.0';

export const DEFAULT_GEOMETRY = {
  a: 6,
  b: 8,
  c: 10
};

export const TACTIC_EXPLANATIONS = [
  'Initialize theorem context with positive side lengths a > 0, b > 0, c > 0 and outer dissection area equality.',
  'Expand algebraic square (a + b)² into a² + 2*a*b + b² using the `ring` tactic.',
  'Simplify 4-fold triangle summation: 4 * ((1 / 2 : ℝ) * a * b) = 2 * a * b via `ring_nf`.',
  'Substitute expanded algebraic and triangular identities into the outer dissection equality.',
  'Apply linear combination on the dissection identity to cancel cross-terms 2*a*b, establishing a² + b² = c².',
  'Conclude Q.E.D. with exact cancellation proof.'
];