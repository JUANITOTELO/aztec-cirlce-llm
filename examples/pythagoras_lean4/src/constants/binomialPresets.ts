export const BINOMIAL_DEFAULT_GEOMETRY = {
  a: 5,
  b: 3
} as const;

export const BINOMIAL_COLOR_PALETTE = {
  whole: 'rgba(99, 102, 241, 0.25)',
  squareA: 'rgba(59, 130, 246, 0.40)', // Sky blue a² (top-left)
  squareB: 'rgba(16, 185, 129, 0.40)', // Emerald green b² (bottom-right)
  rect1: 'rgba(245, 158, 11, 0.40)',   // Amber a·b (top-right)
  rect2: 'rgba(168, 85, 247, 0.40)',   // Purple b·a (bottom-left)
} as const;

export const BINOMIAL_TACTIC_EXPLANATIONS = [
  'Initialize theorem context with positive real lengths a > 0 and b > 0.',
  'Partition outer square (a + b)² along coordinate lines x=a and y=b into 4 planar regions (Euclid II.4 / Yang Hui).',
  'Dissect the geometric grid into primary squares a² (top-left) and b² (bottom-right).',
  'Identify the two rectangular cross-terms of area a·b (top-right) and b·a (bottom-left).',
  'Unify symmetric rectangular cross-terms via real multiplication commutativity (b·a = a·b): a·b + b·a = 2·a·b.',
  'Assemble algebraic partition terms: (a + b)² = a² + 2*a*b + b² certified by Lean 4 ring tactic.'
];
