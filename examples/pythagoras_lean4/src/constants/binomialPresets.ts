export const BINOMIAL_DEFAULT_GEOMETRY = {
  a: 5,
  b: 3
} as const;

export const BINOMIAL_COLOR_PALETTE = {
  whole: 'rgba(99, 102, 241, 0.25)',
  squareA: 'rgba(59, 130, 246, 0.35)', // Sky blue a²
  squareB: 'rgba(16, 185, 129, 0.35)', // Emerald green b²
  rect1: 'rgba(245, 158, 11, 0.35)',   // Amber ab upper-right
  rect2: 'rgba(168, 85, 247, 0.35)',   // Purple ab lower-left
  tri1: 'rgba(245, 158, 11, 0.4)',    // Amber ab/2 upper
  tri2: 'rgba(249, 115, 22, 0.4)',    // Orange ab/2 upper
  tri3: 'rgba(168, 85, 247, 0.4)',    // Purple ab/2 lower
  tri4: 'rgba(236, 72, 153, 0.4)'     // Pink ab/2 lower
} as const;

export const BINOMIAL_TACTIC_EXPLANATIONS = [
  'Initialize theorem context with positive real lengths a > 0 and b > 0.',
  'Formulate whole geometric partition of square (a + b)² with a 45° diagonal bisector.',
  'Dissect the (a + b)² plane into diagonal squares a², b² and two a×b rectangles.',
  'Apply diagonal cuts across both rectangles yielding 4 congruent right triangles of area (1/2)*ab.',
  'Sum the 4 triangular regions: 4 * ((1/2) * a * b) = 2*a*b via ring equivalence.',
  'Assemble algebraic partition terms: (a + b)² = a² + 2*a*b + b² certified by Lean 4 ring tactic.'
];
