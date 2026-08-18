export const GOUGU_DEFAULT_GEOMETRY = {
  a: 3,
  b: 4,
  c: 5
};

export const GOUGU_COLOR_PALETTE = {
  triangle1: 'rgba(239, 68, 68, 0.75)',   // Vermilion 1 (Zhu Shi)
  triangle2: 'rgba(249, 115, 22, 0.75)',  // Vermilion 2 (Zhu Shi)
  triangle3: 'rgba(234, 88, 12, 0.75)',   // Vermilion 3 (Zhu Shi)
  triangle4: 'rgba(194, 65, 12, 0.75)',   // Vermilion 4 (Zhu Shi)
  centerSquare: 'rgba(234, 179, 8, 0.85)', // Yellow center square (Huang Fang)
  hypotSquare: 'rgba(168, 85, 247, 0.25)', // Hypotenuse square boundary (Xian Mi)
  gridLine: 'rgba(148, 163, 184, 0.15)'
};

export const GOUGU_TACTIC_EXPLANATIONS = [
  'Initialize Zhao Shuang Gougu hypotheses with positive legs Gou (a), Gu (b), Xian (c) and Xian Tu identity.',
  'Expand the central Yellow Square (Huang Fang, (gu - gou)²) into gu² - 2*gu*gou + gou² via `ring`.',
  'Simplify the 4 Vermilion Triangles (Zhu Shi): 4 * ((1 / 2 : ℝ) * gou * gu) = 2 * gou * gu via `ring_nf`.',
  'Substitute expanded identities into the Hypotenuse Diagram area equality.',
  'Apply linear combination on the Xian Tu identity to cancel cross-terms 2*gou*gu, establishing gou² + gu² = xian².',
  'Conclude Q.E.D. with exact cancellation proof.'
];
