import { useEffect } from 'react';
import { useProofStore } from './useProofStore';

export function useDissectionAnimation(): void {
  const { state, tacticStates, setStepIndex, togglePlaying } = useProofStore();
  const { isPlaying, activeStepIndex, playbackSpeed } = state;

  useEffect(() => {
    if (!isPlaying) return;

    const interval = setInterval(() => {
      if (activeStepIndex >= tacticStates.length - 1) {
        togglePlaying();
      } else {
        setStepIndex(activeStepIndex + 1);
      }
    }, 1800 / playbackSpeed);

    return () => clearInterval(interval);
  }, [isPlaying, activeStepIndex, tacticStates.length, playbackSpeed, setStepIndex, togglePlaying]);
}