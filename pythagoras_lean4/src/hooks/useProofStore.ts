import { useState, useEffect } from 'react';
import { proofStore } from '../store/proofStore';
import { ProofAppState } from '../types/proofState';
import { LeanTacticState } from '../types/lean';

export function useProofStore(): {
  state: ProofAppState;
  tacticStates: readonly LeanTacticState[];
  setGeometry: (a: number, b: number) => void;
  setStepIndex: (idx: number) => void;
  setMode: (mode: 'rearrangement' | 'zhoubi_suanjing') => void;
  togglePlaying: () => void;
  setShowImplicits: (show: boolean) => void;
  setPlaybackSpeed: (speed: number) => void;
} {
  const [state, setState] = useState<ProofAppState>(proofStore.getState());
  const [tacticStates, setTacticStates] = useState<readonly LeanTacticState[]>(
    proofStore.getTacticStates()
  );

  useEffect(() => {
    const unsubscribe = proofStore.subscribe(() => {
      setState(proofStore.getState());
      setTacticStates(proofStore.getTacticStates());
    });
    return unsubscribe;
  }, []);

  return {
    state,
    tacticStates,
    setGeometry: proofStore.setGeometry.bind(proofStore),
    setStepIndex: proofStore.setStepIndex.bind(proofStore),
    setMode: proofStore.setMode.bind(proofStore),
    togglePlaying: proofStore.togglePlaying.bind(proofStore),
    setShowImplicits: proofStore.setShowImplicits.bind(proofStore),
    setPlaybackSpeed: proofStore.setPlaybackSpeed.bind(proofStore)
  };
}