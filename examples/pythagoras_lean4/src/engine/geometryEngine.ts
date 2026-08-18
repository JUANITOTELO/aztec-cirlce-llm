import { GeometryParams, DissectionMode, TheoremType } from '../types/proofState';
import { DissectionFrame, TriangleShape, SquareShape } from '../types/geometry';
import { sanitizeNumber } from '../utils/sanitizer';
import { computeProofHash } from '../utils/cryptoHash';
import { COLOR_PALETTE } from '../constants/pythagorasData';
import { buildBinomialDissectionFrame } from './binomialEngine';
import { buildGouguDissectionFrame } from './gouguEngine';

export function validateGeometry(a: number, b: number, theorem: TheoremType = 'pythagoras'): GeometryParams {
  const defaultA = theorem === 'binomial' ? 5 : 3;
  const defaultB = theorem === 'binomial' ? 3 : 4;
  const safeA = sanitizeNumber(a, defaultA);
  const safeB = sanitizeNumber(b, defaultB);
  const c = theorem !== 'binomial' ? Math.sqrt(safeA * safeA + safeB * safeB) : undefined;

  if (safeA <= 0 || safeB <= 0) {
    return { a: safeA, b: safeB, c, isValid: false, validationError: 'Dimensions must be positive' };
  }
  return {
    a: safeA,
    b: safeB,
    c: c !== undefined ? Math.round(c * 1000) / 1000 : undefined,
    isValid: true
  };
}

export function buildDissectionFrame(
  params: GeometryParams,
  stepIndex: number,
  mode: DissectionMode,
  theorem: TheoremType = 'pythagoras'
): DissectionFrame {
  if (theorem === 'binomial') {
    return buildBinomialDissectionFrame(params, stepIndex);
  }
  if (theorem === 'gougu') {
    return buildGouguDissectionFrame(params, stepIndex);
  }

  const { a, b, c = Math.sqrt(a * a + b * b) } = params;
  const scale = 20;
  const sa = a * scale;
  const sb = b * scale;
  const total = sa + sb;
  const pad = 20;

  const triangles: TriangleShape[] = [];
  const squares: SquareShape[] = [];

  if (mode === 'zhoubi_suanjing' || stepIndex >= 1) {
    triangles.push(
      { id: 1, points: [{ x: pad, y: pad }, { x: pad + sa, y: pad }, { x: pad, y: pad + sb }], color: COLOR_PALETTE.triangle1, label: 'T₁' },
      { id: 2, points: [{ x: pad + total, y: pad }, { x: pad + total, y: pad + sa }, { x: pad + sa, y: pad }], color: COLOR_PALETTE.triangle2, label: 'T₂' },
      { id: 3, points: [{ x: pad + total, y: pad + total }, { x: pad + sb, y: pad + total }, { x: pad + total, y: pad + sa }], color: COLOR_PALETTE.triangle3, label: 'T₃' },
      { id: 4, points: [{ x: pad, y: pad + total }, { x: pad, y: pad + sb }, { x: pad + sb, y: pad + total }], color: COLOR_PALETTE.triangle4, label: 'T₄' }
    );

    if (stepIndex >= 2) {
      squares.push({
        id: 'c2',
        points: [{ x: pad + sa, y: pad }, { x: pad + total, y: pad + sa }, { x: pad + sb, y: pad + total }, { x: pad, y: pad + sb }],
        color: COLOR_PALETTE.squareC,
        label: `c² = ${Math.round(c * c)}`,
        area: c * c
      });
    }
  } else {
    triangles.push({
      id: 1,
      points: [{ x: pad, y: pad }, { x: pad + sa, y: pad }, { x: pad, y: pad + sb }],
      color: COLOR_PALETTE.triangle1,
      label: 'Δ(a,b,c)'
    });
  }

  const checksum = computeProofHash(`pythagoras:${a}:${b}:${c}:${stepIndex}:${mode}`);
  return {
    triangles,
    squares,
    outerDimension: total + pad * 2,
    description: `Dissection configuration at tactic step ${stepIndex}`,
    proofStepIndex: stepIndex,
    checksum
  };
}
