import { GeometryParams } from '../types/proofState';
import { DissectionFrame, TriangleShape, SquareShape } from '../types/geometry';
import { BINOMIAL_COLOR_PALETTE, BINOMIAL_TACTIC_EXPLANATIONS } from '../constants/binomialPresets';
import { computeProofHash } from '../utils/cryptoHash';

export function buildBinomialDissectionFrame(
  params: GeometryParams,
  stepIndex: number
): DissectionFrame {
  const { a, b } = params;
  const scale = 260 / (a + b);
  const sa = a * scale;
  const sb = b * scale;
  const total = sa + sb;
  const pad = 20;

  const triangles: TriangleShape[] = [];
  const squares: SquareShape[] = [];

  const sqA: SquareShape = {
    id: 'a2',
    points: [
      { x: pad, y: pad },
      { x: pad + sa, y: pad },
      { x: pad + sa, y: pad + sa },
      { x: pad, y: pad + sa }
    ],
    color: BINOMIAL_COLOR_PALETTE.squareA,
    label: `a² = ${a * a}`,
    area: a * a
  };

  const sqB: SquareShape = {
    id: 'b2',
    points: [
      { x: pad + sa, y: pad + sa },
      { x: pad + total, y: pad + sa },
      { x: pad + total, y: pad + total },
      { x: pad + sa, y: pad + total }
    ],
    color: BINOMIAL_COLOR_PALETTE.squareB,
    label: `b² = ${b * b}`,
    area: b * b
  };

  const rect1: SquareShape = {
    id: 'rect1',
    points: [
      { x: pad + sa, y: pad },
      { x: pad + total, y: pad },
      { x: pad + total, y: pad + sa },
      { x: pad + sa, y: pad + sa }
    ],
    color: BINOMIAL_COLOR_PALETTE.rect1,
    label: `a·b = ${a * b}`,
    area: a * b
  };

  const rect2: SquareShape = {
    id: 'rect2',
    points: [
      { x: pad, y: pad + sa },
      { x: pad + sa, y: pad + sa },
      { x: pad + sa, y: pad + total },
      { x: pad, y: pad + total }
    ],
    color: BINOMIAL_COLOR_PALETTE.rect2,
    label: stepIndex >= 4 ? `a·b = ${a * b}` : `b·a = ${b * a}`,
    area: a * b
  };

  if (stepIndex === 0) {
    // Step 0: Whole initial square (a+b)²
    squares.push({
      id: 'whole',
      points: [
        { x: pad, y: pad },
        { x: pad + total, y: pad },
        { x: pad + total, y: pad + total },
        { x: pad, y: pad + total }
      ],
      color: BINOMIAL_COLOR_PALETTE.whole,
      label: `(a+b)² = ${(a + b) * (a + b)}`,
      area: (a + b) * (a + b)
    });
  } else if (stepIndex === 1) {
    // Step 1: 4 grid partition outline
    squares.push(
      { ...sqA, color: 'rgba(59, 130, 246, 0.20)', label: 'a²' },
      { ...sqB, color: 'rgba(16, 185, 129, 0.20)', label: 'b²' },
      { ...rect1, color: 'rgba(245, 158, 11, 0.20)', label: 'a·b' },
      { ...rect2, color: 'rgba(168, 85, 247, 0.20)', label: 'b·a' }
    );
  } else if (stepIndex === 2) {
    // Step 2: Highlight squares a² and b²
    squares.push(sqA, sqB);
  } else if (stepIndex === 3) {
    // Step 3: Identify rectangles a·b and b·a
    squares.push(sqA, sqB, rect1, rect2);
  } else if (stepIndex === 4) {
    // Step 4: Unify symmetric rectangular cross terms 2·a·b
    squares.push(sqA, sqB, rect1, rect2);
  } else {
    // Step 5: Fully assembled algebraic identity (a+b)² = a² + 2ab + b²
    squares.push(sqA, sqB, rect1, rect2);
  }

  const checksum = computeProofHash(`binomial:${a}:${b}:${stepIndex}`);
  const description = BINOMIAL_TACTIC_EXPLANATIONS[stepIndex] ?? `Binomial (a+b)² geometric dissection (Euclid II.4) at step ${stepIndex}`;

  return {
    triangles,
    squares,
    outerDimension: total + pad * 2,
    description,
    proofStepIndex: stepIndex,
    checksum
  };
}
