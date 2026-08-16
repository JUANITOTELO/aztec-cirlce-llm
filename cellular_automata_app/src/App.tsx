import { useCallback, useState } from 'react';
import { Toolbar } from './components/Toolbar';
import { MetricsBar } from './components/MetricsBar';
import { SimulationCanvas } from './components/SimulationCanvas';
import { useSimulationWorker } from './hooks/useSimulationWorker';
import { AutomataRule, Point, Preset } from './types/simulation';
import { PRESETS } from './constants/presets';
import { SIMULATION_DIMENSIONS } from './constants/config';

export default function App() {
  const [isPlaying, setIsPlaying] = useState(true);
  const [rule, setRule] = useState<AutomataRule>('game-of-life');
  const [speed, setSpeed] = useState(30);

  const { postMessage, metrics } = useSimulationWorker();

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
  }, [postMessage]);

  const handlePresetChange = useCallback((presetName: string) => {
    const preset = PRESETS[rule]?.find(p => p.name === presetName);
    if (preset) {
      // Basic validation to mitigate security risk of malformed presets
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

  const handleDraw = useCallback((points: Point[]) => {
    postMessage({ type: 'draw', points });
  }, [postMessage]);

  return (
    <div className="flex flex-col h-screen bg-gray-800 font-sans">
      <Toolbar
        isPlaying={isPlaying}
        rule={rule}
        speed={speed}
        onPlayPause={handlePlayPause}
        onStep={handleStep}
        onRuleChange={handleRuleChange}
        onPresetChange={handlePresetChange}
        onSpeedChange={handleSpeedChange}
      />
      <main className="flex-grow relative bg-gray-900">
        <SimulationCanvas
          width={SIMULATION_DIMENSIONS.width}
          height={SIMULATION_DIMENSIONS.height}
          onDraw={handleDraw}
        />
      </main>
      <MetricsBar metrics={metrics} />
    </div>
  );
}
