/**
 * Gets the state of a cell, handling fixed boundary conditions.
 * Cells outside the grid are considered state 0.
 */
function getCellState(x: number, y: number, width: number, grid: Uint8Array): number {
  if (x < 0 || x >= width) {
    return 0;
  }
  return grid[y * width + x];
}

/**
 * Computes the next state of a cell based on the Rule 110 ruleset.
 * Exported for testing.
 */
export function getNextState(left: number, middle: number, right: number): number {
  const index = (left << 2) | (middle << 1) | right;
  // Rule 110 in binary is 01101110. We read from right to left.
  const rule110 = 0b01101110;
  return (rule110 >> index) & 1;
}

/**
 * Computes the next state for Elementary Rule 110.
 * This implementation assumes a fixed boundary (outside is always 0).
 * @returns An array of cells that changed state.
 */
export function stepRule110(
  width: number,
  height: number,
  readGrid: Uint8Array,
  writeGrid: Uint8Array,
  generation: number,
) {
  const changedCells: { x: number; y: number; state: number }[] = [];
  let population = 0;

  // Rule 110 only evolves downwards, so we write to the next line
  const y = generation % height;
  const nextY = (y + 1) % height;

  // Clear the next line before writing to it
  for (let x = 0; x < width; x++) {
    const nextIndex = nextY * width + x;
    if (writeGrid[nextIndex] !== 0) {
      writeGrid[nextIndex] = 0;
      changedCells.push({ x, y: nextY, state: 0 });
    }
  }

  for (let x = 0; x < width; x++) {
    const left = getCellState(x - 1, y, width, readGrid);
    const middle = getCellState(x, y, width, readGrid);
    const right = getCellState(x + 1, y, width, readGrid);

    const nextState = getNextState(left, middle, right);
    const nextIndex = nextY * width + x;

    if (nextState === 1) {
      writeGrid[nextIndex] = 1;
      changedCells.push({ x, y: nextY, state: 1 });
    }
  }

  // Recalculate total population
  for (let i = 0; i < readGrid.length; i++) {
    if (readGrid[i] === 1) population++;
  }

  return { changedCells, population };
}
