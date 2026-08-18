import React, { useMemo } from 'react';
import { GeometryParams, DissectionMode, TheoremType } from '../types/proofState';
import { buildDissectionFrame } from '../engine/geometryEngine';
import { pointsToSvgPath } from '../utils/sanitizer';
import { Card } from '../atoms/Card';
import { Badge } from '../atoms/Badge';

interface DissectionCanvasProps {
  params: GeometryParams;
  stepIndex: number;
  mode: DissectionMode;
  theorem: TheoremType;
}

export const DissectionCanvas: React.FC<DissectionCanvasProps> = ({ params, stepIndex, mode, theorem }) => {
  const frame = useMemo(() => {
    return buildDissectionFrame(params, stepIndex, mode, theorem);
  }, [params, stepIndex, mode, theorem]);

  const canvasSize = 300;

  return (
    <Card
      title={theorem === 'pythagoras' ? 'Pythagorean Geometric Dissection' : 'Binomial 45° Diagonal Slicing'}
      subtitle={`Tactic Step ${stepIndex} • Dimensions: a=${params.a}, b=${params.b}${params.c ? `, c=${params.c}` : ''}`}
      action={<Badge variant="info">SVG 2D RENDERER</Badge>}
    >
      <div className="flex flex-col items-center justify-center p-4 bg-slate-950/60 rounded-lg border border-slate-800/60">
        <svg
          viewBox={`0 0 ${frame.outerDimension} ${frame.outerDimension}`}
          className="w-full max-w-[280px] h-[280px] drop-shadow-md transition-all duration-300"
        >
          {/* Outer Boundary Frame */}
          <rect
            x={20}
            y={20}
            width={frame.outerDimension - 40}
            height={frame.outerDimension - 40}
            fill="none"
            stroke="rgba(148, 163, 184, 0.2)"
            strokeWidth={1.5}
            strokeDasharray="4 4"
          />

          {/* Sub-squares */}
          {frame.squares.map((sq) => (
            <path
              key={sq.id}
              d={pointsToSvgPath(sq.points)}
              fill={sq.color}
              stroke="rgba(255, 255, 255, 0.4)"
              strokeWidth={1.5}
              className="transition-all duration-300"
            />
          ))}

          {/* Sub-triangles */}
          {frame.triangles.map((tri) => (
            <path
              key={tri.id}
              d={pointsToSvgPath(tri.points)}
              fill={tri.color}
              stroke="rgba(255, 255, 255, 0.3)"
              strokeWidth={1.5}
              className="transition-all duration-300"
            />
          ))}

          {/* Centered Labels for triangles */}
          {frame.triangles.map((tri) => {
            const cx = tri.points.reduce((acc, p) => acc + p.x, 0) / tri.points.length;
            const cy = tri.points.reduce((acc, p) => acc + p.y, 0) / tri.points.length;
            return (
              <text
                key={`txt-${tri.id}`}
                x={cx}
                y={cy}
                fill="#f8fafc"
                fontSize={10}
                fontWeight="bold"
                textAnchor="middle"
                dominantBaseline="middle"
                className="pointer-events-none drop-shadow"
              >
                {tri.label}
              </text>
            );
          })}

          {/* Centered Labels for squares */}
          {frame.squares.map((sq) => {
            const cx = sq.points.reduce((acc, p) => acc + p.x, 0) / sq.points.length;
            const cy = sq.points.reduce((acc, p) => acc + p.y, 0) / sq.points.length;
            return (
              <text
                key={`txt-${sq.id}`}
                x={cx}
                y={cy}
                fill="#f8fafc"
                fontSize={11}
                fontWeight="bold"
                textAnchor="middle"
                dominantBaseline="middle"
                className="pointer-events-none drop-shadow"
              >
                {sq.label}
              </text>
            );
          })}
        </svg>

        <p className="text-xs text-slate-400 mt-2 font-mono">{frame.description}</p>
      </div>
    </Card>
  );
};
