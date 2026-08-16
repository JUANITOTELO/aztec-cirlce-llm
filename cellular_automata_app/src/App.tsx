import { useCallback, useEffect, useState } from 'react';
import { Toolbar } from './components/Toolbar';
import { MetricsBar } from './components/MetricsBar';
import { SimulationCanvas } from './components/SimulationCanvas';
import { useSimulationWorker } from './hooks/useSimulationWorker';
import { AutomataRule, Point } from './types/simulation';
import { PRESETS } from './constants/presets';
import { SIMULATION_DIMENSIONS } from './constants/config';

export default function App() {
  const [isPlaying, setIsPlaying] = useState(true);
  const [rule, setRule] = useState<AutomataRule>('game-of-life');
  const [speed, setSpeed] = useState(30);
  const [resolution, setResolution] = useState(SIMULATION_DIMENSIONS.width);

  const { postMessage, metrics, worker } = useSimulationWorker();

  useEffect(() => {
    const defaultPreset = PRESETS['game-of-life']?.[0];
    if (defaultPreset) {
      postMessage({ type: 'load-preset', preset: defaultPreset });
    }
  }, [postMessage]);

  const handlePlayPause = useCallback(() => {
    const newIsPlaying = !isPlaying;
    setIsPlaying(newIsPlaying);
    postMessage({ type: newIsPlaying ? 'play' : 'pause' });
  }, [isPlaying, postMessage]);

  const handleStep = useCallback(() => {
    setIsPlaying(false);
    postMessage({ type: 'step' });
  }, [postMessage]);

  const handleRuleChange = useCallback((newRule: AutomataRule) => {
    setRule(newRule);
    postMessage({ type: 'set-rule', rule: newRule });
    const defaultPreset = PRESETS[newRule]?.[0];
    if (defaultPreset) {
      postMessage({ type: 'load-preset', preset: defaultPreset });
    }
  }, [postMessage]);

  const handlePresetChange = useCallback((presetName: string) => {
    const preset = PRESETS[rule]?.find(p => p.name === presetName);
    if (preset) {
      if (preset.version !== 1 || !Array.isArray(preset.pattern)) {
        console.error('Invalid preset format');
        return;
      }
      postMessage({ type: 'load-preset', preset });
    }
  }, [rule, postMessage]);

  const handleSpeedChange = useCallback((newSpeed: number) => {
    setSpeed(newSpeed);
    postMessage({ type: 'set-speed', speed: newSpeed });
  }, [postMessage]);

  const handleResolutionChange = useCallback((newResolution: number) => {
    setResolution(newResolution);
    postMessage({ type: 'init', width: newResolution, height: newResolution });
    const defaultPreset = PRESETS[rule]?.[0];
    if (defaultPreset) {
      postMessage({ type: 'load-preset', preset: defaultPreset });
    }
    if (isPlaying) {
      postMessage({ type: 'play' });
    }
  }, [rule, isPlaying, postMessage]);

  const handleDraw = useCallback((points: Point[]) => {
    postMessage({ type: 'draw', points });
  }, [postMessage]);

  return (
    <div className="flex flex-col h-screen bg-gray-800 font-sans">
      <Toolbar
        isPlaying={isPlaying}
        rule={rule}
        speed={speed}
        resolution={resolution}
        onPlayPause={handlePlayPause}
        onStep={handleStep}
        onRuleChange={handleRuleChange}
        onPresetChange={handlePresetChange}
        onSpeedChange={handleSpeedChange}
        onResolutionChange={handleResolutionChange}
      />
      <main className="flex-1 min-h-0 relative bg-gray-900">
        <SimulationCanvas
          width={resolution}
          height={resolution}
          onDraw={handleDraw}
          worker={worker}
        />
      </main>
      <MetricsBar metrics={metrics} />
    </div>
  );
}
