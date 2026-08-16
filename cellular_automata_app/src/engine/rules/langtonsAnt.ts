import { Ant, Direction } from '../../types/simulation';

/**
 * Calculates the next state of an ant based on the cell color.
 * Exported for testing.
 */
export function getNextAntState(ant: Ant, cellState: number, width: number): Ant {
  const newAnt = { ...ant };
  // On a white cell (0), turn 90° right
  if (cellState === 0) {
    newAnt.dir = (newAnt.dir + 1) % 4;
  } else {
    // On a black cell (1), turn 90° left
    newAnt.dir = (newAnt.dir - 1 + 4) % 4;
  }

  // Move forward one unit
  switch (newAnt.dir) {
    case Direction.UP: newAnt.y--; break;
    case Direction.RIGHT: newAnt.x++; break;
    case Direction.DOWN: newAnt.y++; break;
    case Direction.LEFT: newAnt.x--; break;
  }
  return newAnt;
}

/**
 * Computes the next state for Langton's Ant.
 * This implementation uses a single ant.
 * @returns An array of cells that changed state.
 */
export function stepLangtonsAnt(
  width: number,
  height: number,
  grid: Uint8Array,
  ant: Ant,
) {
  const changedCells: { x: number; y: number; state: number }[] = [];

  // Wrap ant position to stay within bounds (toroidal grid)
  ant.x = (ant.x + width) % width;
  ant.y = (ant.y + height) % height;

  const index = ant.y * width + ant.x;
  const currentCellState = grid[index];

  // Flip the color of the current cell
  const newCellState = currentCellState === 0 ? 1 : 0;
  grid[index] = newCellState;
  changedCells.push({ x: ant.x, y: ant.y, state: newCellState });

  // Update ant state based on the *original* cell color
  const nextAnt = getNextAntState(ant, currentCellState, width);
  ant.x = nextAnt.x;
  ant.y = nextAnt.y;
  ant.dir = nextAnt.dir;

  // Population is always 1 for a single ant
  const population = grid.reduce((a, b) => a + b, 0);

  return { changedCells, population };
}
