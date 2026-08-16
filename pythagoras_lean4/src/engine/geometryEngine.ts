import { GeometryParams, DissectionMode } from '../types/proofState';
import { DissectionFrame, TriangleShape, SquareShape } from '../types/geometry';
import { sanitizeNumber } from '../utils/sanitizer';
import { computeProofHash } from '../utils/cryptoHash';
import { COLOR_PALETTE } from '../constants/pythagorasData';

export function validateGeometry(a: number, b: number): GeometryParams {
  const safeA = sanitizeNumber(a, 3);
  const safeB = sanitizeNumber(b, 4);
  const c = Math.sqrt(safeA * safeA + safeB * safeB);

  if (safeA <= 0 || safeB <= 0) {
    return { a: safeA, b: safeB, c, isValid: false, validationError: 'Sides must be positive' };
  }
  return { a: safeA, b: safeB, c: Math.round(c * 1000) / 1000, isValid: true };
}

export function buildDissectionFrame(
  params: GeometryParams,
  stepIndex: number,
  mode: DissectionMode
): DissectionFrame {
  const { a, b, c } = params;
  const scale = 260 / (a + b);
  const sa = a * scale;
  const sb = b * scale;
  const sc = c * scale;
  const total = sa + sb;
  const pad = 20;

  const triangles: TriangleShape[] = [];
  const squares: SquareShape[] = [];

  if (mode === 'zhoubi_suanjing' || stepIndex >= 1) {
    // 4 rotated triangles around inner c^2 or outer (a+b)^2
    const tProgress = Math.min(1, Math.max(0, stepIndex / 5));
    
    // Positions interpolating between square layout and separated layout
    triangles.push(
      { id: 1, points: [{ x: pad, y: pad + sa }, { x: pad, y: pad + total }, { x: pad + sb, y: pad + total }], color: COLOR_PALETTE.triangle1, label: 'T₁' },
      { id: 2, points: [{ x: pad + sb, y: pad + total }, { x: pad + total, y: pad + total }, { x: pad + total, y: pad + sb }], color: COLOR_PALETTE.triangle2, label: 'T₂' },
      { id: 3, points: [{ x: pad + total, y: pad + sb }, { x: pad + total, y: pad }, { x: pad + sa, y: pad }], color: COLOR_PALETTE.triangle3, label: 'T₃' },
      { id: 4, points: [{ x: pad + sa, y: pad }, { x: pad, y: pad }, { x: pad, y: pad + sa }], color: COLOR_PALETTE.triangle4, label: 'T₄' }
    );

    if (stepIndex >= 2) {
      squares.push({
        id: 'c2',
        points: [
          { x: pad, y: pad + sa },
          { x: pad + sb, y: pad + total },
          { x: pad + total, y: pad + sb },
          { x: pad + sa, y: pad }
        ],
        color: COLOR_PALETTE.squareC,
        label: `c² = ${Math.round(c * c)}`,
        area: c * c
      });
    }
  } else {
    // Base Right Triangle
    triangles.push({
      id: 1,
      points: [{ x: pad + sb, y: pad + total }, { x: pad + total, y: pad + total }, { x: pad + total, y: pad + sb }],
      color: COLOR_PALETTE.triangle1,
      label: 'Δ(a,b,c)'
    });
  }

  const checksum = computeProofHash(`${a}:${b}:${c}:${stepIndex}:${mode}`);

  return {
    triangles,
    squares,
    outerDimension: total + pad * 2,
    description: `Dissection configuration at tactic step ${stepIndex}`,
    proofStepIndex: stepIndex,
    checksum
  };
}