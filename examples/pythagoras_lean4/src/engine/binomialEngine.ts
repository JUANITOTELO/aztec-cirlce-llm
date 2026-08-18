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
  } else if (stepIndex === 1 || stepIndex === 2) {
    // Steps 1 & 2: Dissection into a², b² and two a×b rectangles
    squares.push(
      {
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
      },
      {
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
      },
      {
        id: 'rect1',
        points: [
          { x: pad + sa, y: pad },
          { x: pad + total, y: pad },
          { x: pad + total, y: pad + sa },
          { x: pad + sa, y: pad + sa }
        ],
        color: BINOMIAL_COLOR_PALETTE.rect1,
        label: `ab = ${a * b}`,
        area: a * b
      },
      {
        id: 'rect2',
        points: [
          { x: pad, y: pad + sa },
          { x: pad + sa, y: pad + sa },
          { x: pad + sa, y: pad + total },
          { x: pad, y: pad + total }
        ],
        color: BINOMIAL_COLOR_PALETTE.rect2,
        label: `ab = ${a * b}`,
        area: a * b
      }
    );
  } else {
    // Steps 3, 4, 5: a², b² plus 4 diagonally sliced right triangles (ab/2 each)
    squares.push(
      {
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
      },
      {
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
      }
    );

    // Upper-Right Rectangle sliced diagonally
    triangles.push(
      {
        id: 101,
        points: [
          { x: pad + sa, y: pad },
          { x: pad + total, y: pad },
          { x: pad + total, y: pad + sa }
        ],
        color: BINOMIAL_COLOR_PALETTE.tri1,
        label: 'ab/2'
      },
      {
        id: 102,
        points: [
          { x: pad + sa, y: pad },
          { x: pad + total, y: pad + sa },
          { x: pad + sa, y: pad + sa }
        ],
        color: BINOMIAL_COLOR_PALETTE.tri2,
        label: 'ab/2'
      }
    );

    // Lower-Left Rectangle sliced diagonally
    triangles.push(
      {
        id: 103,
        points: [
          { x: pad, y: pad + sa },
          { x: pad + sa, y: pad + sa },
          { x: pad, y: pad + total }
        ],
        color: BINOMIAL_COLOR_PALETTE.tri3,
        label: 'ab/2'
      },
      {
        id: 104,
        points: [
          { x: pad + sa, y: pad + sa },
          { x: pad + sa, y: pad + total },
          { x: pad, y: pad + total }
        ],
        color: BINOMIAL_COLOR_PALETTE.tri4,
        label: 'ab/2'
      }
    );
  }

  const checksum = computeProofHash(`binomial:${a}:${b}:${stepIndex}`);
  const description = BINOMIAL_TACTIC_EXPLANATIONS[stepIndex] ?? `Binomial (a+b)² diagonal dissection at step ${stepIndex}`;

  return {
    triangles,
    squares,
    outerDimension: total + pad * 2,
    description,
    proofStepIndex: stepIndex,
    checksum
  };
}
