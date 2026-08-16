import React from 'react';
import { Header } from './components/Header';
import { DissectionCanvas } from './components/DissectionCanvas';
import { GeometryControls } from './components/GeometryControls';
import { TacticStateExplorer } from './components/TacticStateExplorer';
import { ProofTreeVisualizer } from './components/ProofTreeVisualizer';
import { LeanCodeGenerator } from './components/LeanCodeGenerator';
import { useProofStore } from './hooks/useProofStore';
import { useDissectionAnimation } from './hooks/useDissectionAnimation';

export const App: React.FC = () => {
  const {
    state,
    tacticStates,
    setGeometry,
    setStepIndex,
    setMode,
    togglePlaying,
    setShowImplicits,
    setPlaybackSpeed
  } = useProofStore();

  useDissectionAnimation();

  const currentTactic = tacticStates[state.activeStepIndex] || tacticStates[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header checksum={state.verifiedChecksum} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Visual Canvas & Geometric Controls */}
        <div className="lg:col-span-6 space-y-6">
          <DissectionCanvas
            params={state.params}
            stepIndex={state.activeStepIndex}
            mode={state.mode}
          />
          <GeometryControls
            params={state.params}
            mode={state.mode}
            isPlaying={state.isPlaying}
            activeStep={state.activeStepIndex}
            maxSteps={tacticStates.length}
            playbackSpeed={state.playbackSpeed}
            onGeometryChange={setGeometry}
            onModeChange={setMode}
            onTogglePlay={togglePlaying}
            onStepNext={() => setStepIndex(state.activeStepIndex + 1)}
            onReset={() => setStepIndex(0)}
            onSpeedChange={setPlaybackSpeed}
          />
        </div>

        {/* Right Column: Lean 4 Tactic Inspector & Code Generator */}
        <div className="lg:col-span-6 space-y-6">
          <TacticStateExplorer
            currentState={currentTactic}
            showImplicits={state.showImplicits}
            onToggleImplicits={setShowImplicits}
          />
          <ProofTreeVisualizer
            states={tacticStates}
            activeIndex={state.activeStepIndex}
            onSelectStep={setStepIndex}
          />
          <LeanCodeGenerator params={state.params} />
        </div>
      </main>
    </div>
  );
};

export default App;
