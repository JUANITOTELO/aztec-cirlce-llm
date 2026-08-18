import { useState, useEffect, useMemo } from 'react';
import { proofStore } from '../store/proofStore';
import { ProofAppState, DissectionMode, TheoremType } from '../types/proofState';
import { LeanKernelSimulator } from '../engine/leanKernelSimulator';

export function useProofStore() {
  const [state, setState] = useState<ProofAppState>(() => proofStore.getState());

  useEffect(() => {
    const unsubscribe = proofStore.subscribe((newState) => {
      setState(newState);
    });
    return () => unsubscribe();
  }, []);

  const tacticStates = useMemo(() => {
    return LeanKernelSimulator.generateTactics(state.params, state.activeTheorem);
  }, [state.params, state.activeTheorem]);

  return {
    state,
    tacticStates,
    setTheorem: (theorem: TheoremType) => proofStore.setTheorem(theorem),
    setGeometry: (a: number, b: number) => proofStore.setGeometry(a, b),
    setStepIndex: (index: number) => proofStore.setStepIndex(index),
    setMode: (mode: DissectionMode) => proofStore.setMode(mode),
    togglePlaying: () => proofStore.togglePlaying(),
    setShowImplicits: (show: boolean) => proofStore.setShowImplicits(show),
    setPlaybackSpeed: (speed: number) => proofStore.setPlaybackSpeed(speed)
  };
}
