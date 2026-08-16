import React from 'react';
import { buildDissectionFrame } from '../engine/geometryEngine';
import { GeometryParams, DissectionMode } from '../types/proofState';
import { pointsToSvgPath } from '../utils/sanitizer';
import { Badge } from '../atoms/Badge';

interface DissectionCanvasProps {
  params: GeometryParams;
  stepIndex: number;
  mode: DissectionMode;
}

export const DissectionCanvas: React.FC<DissectionCanvasProps> = ({ params, stepIndex, mode }) => {
  const frame = buildDissectionFrame(params, stepIndex, mode);
  const dim = frame.outerDimension;

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-slate-950/60 rounded-lg border border-slate-800/80 relative overflow-hidden">
      <div className="absolute top-3 left-3 flex gap-2 z-10">
        <Badge variant="purple">Step {stepIndex + 1} / 6</Badge>
        <Badge variant="neutral">{mode === 'zhoubi_suanjing' ? 'Zhoubi Suanjing' : 'Rearrangement'}</Badge>
      </div>

      <svg
        viewBox={`0 0 ${dim} ${dim}`}
        className="w-full max-w-[380px] h-auto transition-transform duration-500 ease-out drop-shadow-2xl"
      >
        {/* Outer Bounding Grid */}
        <rect
          x={15}
          y={15}
          width={dim - 30}
          height={dim - 30}
          fill="none"
          stroke="#334155"
          strokeDasharray="4 4"
          strokeWidth="1.5"
          rx="4"
        />

        {/* Squares */}
        {frame.squares.map((sq) => (
          <g key={sq.id} className="transition-all duration-700">
            <path
              d={pointsToSvgPath(sq.points)}
              fill={sq.color}
              stroke="#f43f5e"
              strokeWidth="2"
            />
            <text
              x={dim / 2}
              y={dim / 2 + 4}
              textAnchor="middle"
              fill="#ffffff"
              fontSize="12"
              fontFamily="JetBrains Mono, monospace"
              fontWeight="bold"
            >
              {sq.label}
            </text>
          </g>
        ))}

        {/* Triangles */}
        {frame.triangles.map((tr) => (
          <g key={tr.id} className="transition-all duration-700 hover:opacity-90">
            <path
              d={pointsToSvgPath(tr.points)}
              fill={tr.color}
              stroke="#38bdf8"
              strokeWidth="1.5"
            />
          </g>
        ))}
      </svg>

      <div className="mt-3 text-center text-xs font-mono text-slate-400">
        Area Relation: <span className="text-sky-300 font-semibold">({params.a} + {params.b})²</span> ={' '}
        <span className="text-rose-400 font-semibold">{params.c}²</span> + 4·(½·{params.a}·{params.b})
      </div>
    </div>
  );
};