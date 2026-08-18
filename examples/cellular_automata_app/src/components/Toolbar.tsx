import React from 'react';
import { Play, Pause, StepForward } from 'lucide-react';
import { Button } from '../atoms/Button';
import { Select } from '../atoms/Select';
import { Slider } from '../atoms/Slider';
import { AutomataRule } from '../types/simulation';
import { PRESETS } from '../constants/presets';
import { RESOLUTION_OPTIONS } from '../constants/config';

interface ToolbarProps {
  isPlaying: boolean;
  rule: AutomataRule;
  speed: number;
  resolution: number;
  onPlayPause: () => void;
  onStep: () => void;
  onRuleChange: (rule: AutomataRule) => void;
  onPresetChange: (name: string) => void;
  onSpeedChange: (speed: number) => void;
  onResolutionChange: (resolution: number) => void;
}

const RULE_OPTIONS = [
  { value: 'game-of-life', label: "Conway's Game of Life" },
  { value: 'langtons-ant', label: "Langton's Ant" },
  { value: 'rule-110', label: 'Elementary Rule 110' },
];

export const Toolbar: React.FC<ToolbarProps> = ({
  isPlaying,
  rule,
  speed,
  resolution,
  onPlayPause,
  onStep,
  onRuleChange,
  onPresetChange,
  onSpeedChange,
  onResolutionChange,
}) => {
  const presetOptions = PRESETS[rule]?.map((p) => ({ value: p.name, label: p.name })) || [];

  return (
    <header className="bg-gray-900/80 border-b border-gray-700 px-4 py-2 flex items-center space-x-4 z-10">
      <div className="flex items-center space-x-2">
        <Button onClick={onPlayPause} title={isPlaying ? 'Pause' : 'Play'}>
          {isPlaying ? <Pause size={18} /> : <Play size={18} />}
        </Button>
        <Button onClick={onStep} title="Step Forward">
          <StepForward size={18} />
        </Button>
      </div>

      <div className="w-px h-8 bg-gray-700" />

      <div className="flex items-center space-x-2">
        <label className="text-sm text-gray-400">Rule:</label>
        <Select
          value={rule}
          onChange={(e) => onRuleChange(e.target.value as AutomataRule)}
          options={RULE_OPTIONS}
        />
      </div>

      <div className="flex items-center space-x-2">
        <label className="text-sm text-gray-400">Preset:</label>
        <Select
          onChange={(e) => onPresetChange(e.target.value)}
          options={[{ value: '', label: 'Select...' }, ...presetOptions]}
          value=""
        />
      </div>

      <div className="flex items-center space-x-2">
        <label className="text-sm text-gray-400">Resolution:</label>
        <Select
          value={String(resolution)}
          onChange={(e) => onResolutionChange(parseInt(e.target.value, 10))}
          options={RESOLUTION_OPTIONS}
        />
      </div>

      <div className="flex-grow" />

      <div className="flex items-center space-x-2 w-48">
        <label className="text-sm text-gray-400">Speed:</label>
        <Slider
          min="1"
          max="60"
          value={speed}
          onChange={(e) => onSpeedChange(parseInt(e.target.value, 10))}
        />
      </div>
    </header>
  );
};
