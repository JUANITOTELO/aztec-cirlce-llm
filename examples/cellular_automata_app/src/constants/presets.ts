import { Preset } from '../types/simulation';

export const PRESETS: Record<string, Preset[]> = {
  'game-of-life': [
    {
      name: 'Glider',
      version: 1,
      pattern: [
        { x: 1, y: 0 },
        { x: 2, y: 1 },
        { x: 0, y: 2 },
        { x: 1, y: 2 },
        { x: 2, y: 2 },
      ],
    },
    {
      name: 'Pulsar',
      version: 1,
      pattern: [
        { x: 2, y: 0 }, { x: 3, y: 0 }, { x: 4, y: 0 }, { x: 8, y: 0 }, { x: 9, y: 0 }, { x: 10, y: 0 },
        { x: 0, y: 2 }, { x: 5, y: 2 }, { x: 7, y: 2 }, { x: 12, y: 2 },
        { x: 0, y: 3 }, { x: 5, y: 3 }, { x: 7, y: 3 }, { x: 12, y: 3 },
        { x: 0, y: 4 }, { x: 5, y: 4 }, { x: 7, y: 4 }, { x: 12, y: 4 },
        { x: 2, y: 5 }, { x: 3, y: 5 }, { x: 4, y: 5 }, { x: 8, y: 5 }, { x: 9, y: 5 }, { x: 10, y: 5 },
        { x: 2, y: 7 }, { x: 3, y: 7 }, { x: 4, y: 7 }, { x: 8, y: 7 }, { x: 9, y: 7 }, { x: 10, y: 7 },
        { x: 0, y: 8 }, { x: 5, y: 8 }, { x: 7, y: 8 }, { x: 12, y: 8 },
        { x: 0, y: 9 }, { x: 5, y: 9 }, { x: 7, y: 9 }, { x: 12, y: 9 },
        { x: 0, y: 10 }, { x: 5, y: 10 }, { x: 7, y: 10 }, { x: 12, y: 10 },
        { x: 2, y: 12 }, { x: 3, y: 12 }, { x: 4, y: 12 }, { x: 8, y: 12 }, { x: 9, y: 12 }, { x: 10, y: 12 },
      ].map(p => ({ x: p.x + 20, y: p.y + 20 })),
    },
  ],
  'langtons-ant': [
    {
      name: 'Single Ant',
      version: 1,
      pattern: [], // Ant starts at center by default
    },
  ],
  'rule-110': [
    {
      name: 'Single Cell',
      version: 1,
      pattern: [{ x: 256, y: 0 }],
    },
  ],
};
