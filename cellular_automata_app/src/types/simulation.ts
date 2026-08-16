export type AutomataRule = 'game-of-life' | 'langtons-ant' | 'rule-110';

export interface Point {
  x: number;
  y: number;
}

export interface Preset {
  name: string;
  version: 1; // For future-proofing and migration
  pattern: Point[];
}

export enum Direction {
  UP = 0,
  RIGHT = 1,
  DOWN = 2,
  LEFT = 3,
}

export interface Ant {
  x: number;
  y: number;
  dir: Direction;
}

export interface SimulationMetrics {
  generation: number;
  population: number;
}

// Messages from Main Thread to Worker
export type WorkerMessage =
  | { type: 'init'; width: number; height: number }
  | { type: 'play' }
  | { type: 'pause' }
  | { type: 'step' }
  | { type: 'set-rule'; rule: AutomataRule }
  | { type: 'load-preset'; preset: Preset }
  | { type: 'draw'; points: Point[] }
  | { type: 'set-speed'; speed: number };

// Messages from Worker to Main Thread
export type WorkerResponse =
  | { type: 'initialized' }
  | {
      type: 'update';
      changedCells: { x: number; y: number; state: number }[];
      metrics: SimulationMetrics;
    };
