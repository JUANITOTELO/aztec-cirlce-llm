import { useEffect, useState, useRef, useCallback } from 'react';
import { WorkerMessage, SimulationMetrics } from '../types/simulation';
import { SIMULATION_DIMENSIONS } from '../constants/config';

export function useSimulationWorker() {
  const workerRef = useRef<Worker | null>(null);
  const [metrics, setMetrics] = useState<SimulationMetrics>({ generation: 0, population: 0 });

  useEffect(() => {
    // The `as any` is a workaround for Vite's worker handling
    const worker = new Worker(new URL('../engine/worker.ts', import.meta.url), { type: 'module' });
    workerRef.current = worker;
    (window as any).simulationWorker = worker; // Make accessible to canvas for updates

    worker.postMessage({
      type: 'init',
      width: SIMULATION_DIMENSIONS.width,
      height: SIMULATION_DIMENSIONS.height,
    } as WorkerMessage);

    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'update') {
        setMetrics(event.data.metrics);
      }
    };

    worker.addEventListener('message', handleMessage);

    // Mitigation for worker memory leak: terminate on unmount
    return () => {
      worker.terminate();
      workerRef.current = null;
      (window as any).simulationWorker = null;
    };
  }, []);

  const postMessage = useCallback((message: WorkerMessage) => {
    workerRef.current?.postMessage(message);
  }, []);

  return { postMessage, metrics };
}
