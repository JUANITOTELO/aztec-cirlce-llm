import React from 'react';
import { Play, Pause, RotateCcw, FastForward, CheckSquare } from 'lucide-react';
import { Card } from '../atoms/Card';
import { Button } from '../atoms/Button';
import { Slider } from '../atoms/Slider';
import { GeometryParams, DissectionMode, TheoremType } from '../types/proofState';

interface GeometryControlsProps {
  params: GeometryParams;
  mode: DissectionMode;
  theorem: TheoremType;
  isPlaying: boolean;
  activeStep: number;
  maxSteps: number;
  playbackSpeed: number;
  onTheoremChange: (t: TheoremType) => void;
  onGeometryChange: (a: number, b: number) => void;
  onModeChange: (m: DissectionMode) => void;
  onTogglePlay: () => void;
  onStepNext: () => void;
  onReset: () => void;
  onSpeedChange: (s: number) => void;
}

export const GeometryControls: React.FC<GeometryControlsProps> = ({
  params,
  theorem,
  isPlaying,
  activeStep,
  maxSteps,
  playbackSpeed,
  onTheoremChange,
  onGeometryChange,
  onTogglePlay,
  onStepNext,
  onReset,
  onSpeedChange
}) => {
  return (
    <Card title="Theorem & Dissection Parameters" subtitle="Configure formal algebraic & geometric coefficients">
      <div className="space-y-4">
        <div>
          <label className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-1.5 block">Active Theorem</label>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant={theorem === 'pythagoras' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => onTheoremChange('pythagoras')}
            >
              Pythagoras (a² + b² = c²)
            </Button>
            <Button
              variant={theorem === 'binomial' ? 'primary' : 'secondary'}
              size="sm"
              onClick={() => onTheoremChange('binomial')}
            >
              Binomial ((a+b)²)
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Slider
            label="Dimension a"
            value={params.a}
            min={2}
            max={12}
            step={1}
            unit="u"
            onChange={(v) => onGeometryChange(v, params.b)}
          />
          <Slider
            label="Dimension b"
            value={params.b}
            min={2}
            max={12}
            step={1}
            unit="u"
            onChange={(v) => onGeometryChange(params.a, v)}
          />
        </div>

        <div className="flex flex-wrap items-center justify-between pt-2 border-t border-slate-800 gap-3">
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={onTogglePlay}>
              {isPlaying ? <Pause className="w-4 h-4 mr-1 text-amber-400" /> : <Play className="w-4 h-4 mr-1 text-emerald-400" />}
              {isPlaying ? 'Pause' : 'Play'}
            </Button>
            <Button variant="secondary" size="sm" onClick={onStepNext} disabled={activeStep >= maxSteps - 1}>
              <FastForward className="w-4 h-4 mr-1" /> Step
            </Button>
            <Button variant="ghost" size="sm" onClick={onReset}>
              <RotateCcw className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
            <CheckSquare className="w-3.5 h-3.5 text-sky-400" />
            <span>Speed:</span>
            {[1, 2, 4].map((s) => (
              <button
                key={s}
                onClick={() => onSpeedChange(s)}
                className={`px-1.5 py-0.5 rounded ${playbackSpeed === s ? 'bg-sky-500/20 text-sky-300 font-bold' : 'hover:text-slate-200'}`}
              >
                {s}x
              </button>
            ))}
          </div>
        </div>
      </div>
    </Card>
  );
};
