import React from 'react';
import { Play, Pause, RotateCcw, StepForward } from 'lucide-react';
import { Card } from '../atoms/Card';
import { Slider } from '../atoms/Slider';
import { Button } from '../atoms/Button';
import { GeometryParams, DissectionMode } from '../types/proofState';

interface ControlsProps {
  params: GeometryParams;
  mode: DissectionMode;
  isPlaying: boolean;
  activeStep: number;
  maxSteps: number;
  playbackSpeed: number;
  onGeometryChange: (a: number, b: number) => void;
  onModeChange: (m: DissectionMode) => void;
  onTogglePlay: () => void;
  onStepNext: () => void;
  onReset: () => void;
  onSpeedChange: (speed: number) => void;
}

export const GeometryControls: React.FC<ControlsProps> = ({
  params,
  isPlaying,
  activeStep,
  maxSteps,
  playbackSpeed,
  onGeometryChange,
  onTogglePlay,
  onStepNext,
  onReset,
  onSpeedChange
}) => {
  return (
    <Card title="Geometric Dissection Parameters" subtitle="Interactive triangle leg adjustments with kernel sync">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <Slider
            label="Leg a (Base)"
            value={params.a}
            min={2}
            max={12}
            step={1}
            onChange={(a) => onGeometryChange(a, params.b)}
          />
          <Slider
            label="Leg b (Height)"
            value={params.b}
            min={2}
            max={12}
            step={1}
            onChange={(b) => onGeometryChange(params.a, b)}
          />
        </div>

        <Slider
          label="Animation Speed"
          value={playbackSpeed}
          min={0.25}
          max={4}
          step={0.25}
          unit="x"
          onChange={onSpeedChange}
        />

        <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-xs font-mono flex justify-between items-center">
          <span className="text-slate-400">Hypotenuse c = √(a² + b²):</span>
          <span className="text-rose-400 font-bold">{params.c.toFixed(2)}</span>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-slate-800">
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={onTogglePlay}>
              {isPlaying ? <Pause className="w-3.5 h-3.5 mr-1 text-amber-400" /> : <Play className="w-3.5 h-3.5 mr-1 text-green-400" />}
              {isPlaying ? 'Pause' : 'Animate'}
            </Button>
            <Button
              variant="secondary"
              size="sm"
              disabled={activeStep >= maxSteps - 1}
              onClick={onStepNext}
            >
              <StepForward className="w-3.5 h-3.5 mr-1 text-sky-400" />
              Step
            </Button>
          </div>
          <Button variant="ghost" size="sm" onClick={onReset}>
            <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
          </Button>
        </div>
      </div>
    </Card>
  );
};
