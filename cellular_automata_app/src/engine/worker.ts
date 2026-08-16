import { Simulation } from './simulation';
import { WorkerMessage, WorkerResponse } from '../types/simulation';

let simulation: Simulation | null = null;
let intervalId: number | null = null;
let simulationSpeed = 30; // Steps per second

function step() {
  if (!simulation) return;
  const changedCells = simulation.step();
  const response: WorkerResponse = {
    type: 'update',
    changedCells,
    metrics: simulation.metrics,
  };
  postMessage(response);
}

function start() {
  if (intervalId) return;
  const interval = 1000 / simulationSpeed;
  intervalId = self.setInterval(step, interval);
}

function stop() {
  if (intervalId) {
    self.clearInterval(intervalId);
    intervalId = null;
  }
}

function setSpeed(speed: number) {
  simulationSpeed = Math.max(1, speed);
  if (intervalId) {
    stop();
    start();
  }
}

onmessage = (e: MessageEvent<WorkerMessage>) => {
  const msg = e.data;

  switch (msg.type) {
    case 'init':
      simulation = new Simulation(msg.width, msg.height);
      postMessage({ type: 'initialized' });
      start();
      break;
    case 'play':
      start();
      break;
    case 'pause':
      stop();
      break;
    case 'step':
      stop();
      step();
      break;
    case 'set-rule':
      if (!simulation) return;
      const fullGrid = simulation.setRule(msg.rule);
      postMessage({ type: 'update', changedCells: fullGrid, metrics: simulation.metrics });
      break;
    case 'load-preset':
      if (!simulation) return;
      const presetGrid = simulation.loadPreset(msg.preset);
      postMessage({ type: 'update', changedCells: presetGrid, metrics: simulation.metrics });
      break;
    case 'draw':
      if (!simulation) return;
      const drawnCells = simulation.drawPoints(msg.points);
      postMessage({ type: 'update', changedCells: drawnCells, metrics: simulation.metrics });
      break;
    case 'set-speed':
      setSpeed(msg.speed);
      break;
  }
};
