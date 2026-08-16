/**
 * Calculates the number of live neighbors for a cell in a toroidal grid.
 * This function is exported for testing purposes.
 */
export function getNeighborCount(
  x: number,
  y: number,
  width: number,
  height: number,
  grid: Uint8Array,
): number {
  let count = 0;
  for (let i = -1; i <= 1; i++) {
    for (let j = -1; j <= 1; j++) {
      if (i === 0 && j === 0) continue;

      const nx = (x + i + width) % width;
      const ny = (y + j + height) % height;
      const neighborIndex = ny * width + nx;

      if (grid[neighborIndex] === 1) {
        count++;
      }
    }
  }
  return count;
}

/**
 * Computes the next state for Conway's Game of Life.
 * @returns An array of cells that changed state.
 */
export function stepGameOfLife(
  width: number,
  height: number,
  readGrid: Uint8Array,
  writeGrid: Uint8Array,
) {
  const changedCells: { x: number; y: number; state: number }[] = [];
  let population = 0;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const index = y * width + x;
      const cellState = readGrid[index];
      const neighbors = getNeighborCount(x, y, width, height, readGrid);

      let nextState = cellState;
      if (cellState === 1) {
        if (neighbors < 2 || neighbors > 3) {
          nextState = 0; // Death by underpopulation or overpopulation
        }
      } else {
        if (neighbors === 3) {
          nextState = 1; // Birth
        }
      }

      if (nextState === 1) {
        population++;
      }

      if (nextState !== cellState) {
        changedCells.push({ x, y, state: nextState });
      }
      writeGrid[index] = nextState;
    }
  }

  return { changedCells, population };
}
