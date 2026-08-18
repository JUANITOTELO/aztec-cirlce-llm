import { describe, it, expect } from 'vitest';
import { getNeighborCount } from './engine/rules/gameOfLife';
import { getNextAntState } from './engine/rules/langtonsAnt';
import { getNextState as getRule110NextState } from './engine/rules/rule110';
import { Ant, Direction } from './types/simulation';

describe('Cellular Automata Engine Logic', () => {
  it('Game of Life: correctly calculates neighbor count with toroidal wrapping', () => {
    const width = 10;
    const height = 10;
    const grid = new Uint8Array(width * height);
    // Create a 2x2 block at the top-left corner
    grid[0] = 1;
    grid[1] = 1;
    grid[10] = 1;
    grid[11] = 1;

    // Test corner cell (0,0) which should wrap around
    const neighbors = getNeighborCount(0, 0, width, height, grid);
    expect(neighbors).toBe(3);

    // Test cell inside the block
    const neighbors2 = getNeighborCount(1, 1, width, height, grid);
    expect(neighbors2).toBe(3);
  });

  it("Langton's Ant: correctly updates direction and position", () => {
    const ant: Ant = { x: 5, y: 5, dir: Direction.UP };
    const width = 10;

    // On a white cell (0), turn right, move forward
    const nextStateWhite = getNextAntState(ant, 0, width);
    expect(nextStateWhite.dir).toBe(Direction.RIGHT);
    expect(nextStateWhite.x).toBe(6);
    expect(nextStateWhite.y).toBe(5);

    // On a black cell (1), turn left, move forward
    const nextStateBlack = getNextAntState(ant, 1, width);
    expect(nextStateBlack.dir).toBe(Direction.LEFT);
    expect(nextStateBlack.x).toBe(4);
    expect(nextStateBlack.y).toBe(5);
  });

  it('Rule 110: correctly computes next state based on Wolfram definition', () => {
    // Rule 110 (01101110) test cases
    // Neighborhood: 111 -> 0
    expect(getRule110NextState(1, 1, 1)).toBe(0);
    // Neighborhood: 110 -> 1
    expect(getRule110NextState(1, 1, 0)).toBe(1);
    // Neighborhood: 101 -> 1
    expect(getRule110NextState(1, 0, 1)).toBe(1);
    // Neighborhood: 000 -> 0
    expect(getRule110NextState(0, 0, 0)).toBe(0);
  });
});
