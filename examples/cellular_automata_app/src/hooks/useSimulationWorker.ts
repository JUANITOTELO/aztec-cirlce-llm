import { useEffect, useState, useRef, useCallback } from 'react';
import { WorkerMessage, SimulationMetrics } from '../types/simulation';
import { SIMULATION_DIMENSIONS } from '../constants/config';

export function useSimulationWorker() {
  const workerRef = useRef<Worker | null>(null);
  const [worker, setWorker] = useState<Worker | null>(null);
  const [metrics, setMetrics] = useState<SimulationMetrics>({ generation: 0, population: 0 });

  useEffect(() => {
    const simWorker = new Worker(new URL('../engine/worker.ts', import.meta.url), { type: 'module' });
    workerRef.current = simWorker;
    setWorker(simWorker);
    (window as any).simulationWorker = simWorker;

    simWorker.postMessage({
      type: 'init',
      width: SIMULATION_DIMENSIONS.width,
      height: SIMULATION_DIMENSIONS.height,
    } as WorkerMessage);

    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'update') {
        setMetrics(event.data.metrics);
      }
    };

    simWorker.addEventListener('message', handleMessage);

    return () => {
      simWorker.terminate();
      workerRef.current = null;
      setWorker(null);
      (window as any).simulationWorker = null;
    };
  }, []);

  const postMessage = useCallback((message: WorkerMessage) => {
    workerRef.current?.postMessage(message);
  }, []);

  return { postMessage, metrics, worker };
}
