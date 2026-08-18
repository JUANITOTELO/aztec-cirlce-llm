import { GeometryParams } from '../types/proofState';
import { DissectionFrame, TriangleShape, SquareShape, Point2D } from '../types/geometry';
import { computeProofHash } from '../utils/cryptoHash';
import { GOUGU_COLOR_PALETTE } from '../constants/gouguPresets';

export function buildGouguDissectionFrame(params: GeometryParams, stepIndex: number): DissectionFrame {
  const gou = Math.min(params.a, params.b);
  const gu = Math.max(params.a, params.b);
  const c = params.c ?? Math.hypot(gou, gu);
  const pad = 24;
  const total = 260;
  const outerDimension = total + pad * 2;
  const center = outerDimension / 2;
  const scale = total / (gu + gou);
  const d = (gu - gou) / 2;

  // Centered base triangle in standard orientation (勾 = short leg, 股 = long leg)
  // Vertex 0 (outer hypotenuse start): (d + gou, -d)
  // Vertex 1 (inner right angle corner): (d, -d)
  // Vertex 2 (outer hypotenuse tip): (d, -d + gu)
  const baseTriangle = [
    { x: d + gou, y: -d },
    { x: d, y: -d },
    { x: d, y: -d + gu }
  ];

  const triangleColors = [
    GOUGU_COLOR_PALETTE.triangle1,
    GOUGU_COLOR_PALETTE.triangle2,
    GOUGU_COLOR_PALETTE.triangle3,
    GOUGU_COLOR_PALETTE.triangle4
  ];

  // Generate all 4 Zhu Shi (朱实) triangles by cyclic rotation: 0°, 90°, 180°, 270°
  const triangles: TriangleShape[] = [0, 1, 2, 3].map((k) => {
    const theta = (k * Math.PI) / 2;
    const cos = Math.cos(theta);
    const sin = Math.sin(theta);

    const points = baseTriangle.map((pt) => ({
      x: center + (pt.x * cos - pt.y * sin) * scale,
      y: center - (pt.x * sin + pt.y * cos) * scale
    }));

    return {
      id: k + 1,
      points: points as [Point2D, Point2D, Point2D],
      color: triangleColors[k],
      label: `Vermilion ${['₁', '₂', '₃', '₄'][k]}`
    };
  });

  const squares: SquareShape[] = [];
  // Central inner square (黄方)
  if (stepIndex >= 2) {
    const innerSquarePts = [
      { x: -d, y: -d },
      { x: d, y: -d },
      { x: d, y: d },
      { x: -d, y: d }
    ].map((pt) => ({
      x: center + pt.x * scale,
      y: center - pt.y * scale
    })) as [Point2D, Point2D, Point2D, Point2D];

    squares.push({
      id: 'huang_fang',
      points: innerSquarePts,
      color: GOUGU_COLOR_PALETTE.centerSquare,
      label: `Yellow Square (gu-gou)² = ${Math.round((gu - gou) ** 2)}`,
      area: (gu - gou) ** 2
    });
  }

  // Outer tilted square formed by continuous hypotenuses (弦幂)
  if (stepIndex >= 4) {
    const outerSquarePts = [0, 1, 2, 3].map((k) => {
      const theta = (k * Math.PI) / 2;
      const cos = Math.cos(theta);
      const sin = Math.sin(theta);
      const rx = (d + gou) * cos - (-d) * sin;
      const ry = (d + gou) * sin + (-d) * cos;
      return {
        x: center + rx * scale,
        y: center - ry * scale
      };
    }) as [Point2D, Point2D, Point2D, Point2D];

    squares.push({
      id: 'xian_square',
      points: outerSquarePts,
      color: GOUGU_COLOR_PALETTE.hypotSquare,
      label: `Hypotenuse Square c² = ${Math.round(c * c)}`,
      area: c * c
    });
  }

  const checksum = computeProofHash(`gougu:${gou}:${gu}:${c}:${stepIndex}`);
  return {
    triangles,
    squares,
    outerDimension,
    description: `Zhao Shuang Hypotenuse Diagram (Xian Tu) step ${stepIndex}`,
    proofStepIndex: stepIndex,
    checksum
  };
}
