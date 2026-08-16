import { AutomataRule, Point, Preset, Ant, Direction, SimulationMetrics } from '../types/simulation';
import { stepGameOfLife } from './rules/gameOfLife';
import { stepLangtonsAnt } from './rules/langtonsAnt';
import { stepRule110 } from './rules/rule110';

export class Simulation {
  private width: number;
  private height: number;
  private grid: Uint8Array;
  private buffer: Uint8Array;
  private rule: AutomataRule = 'game-of-life';
  private ant: Ant;

  public metrics: SimulationMetrics = { generation: 0, population: 0 };

  constructor(width: number, height: number) {
    this.width = width;
    this.height = height;
    this.grid = new Uint8Array(width * height);
    this.buffer = new Uint8Array(width * height);
    this.ant = this.createDefaultAnt();
  }

  private createDefaultAnt(): Ant {
    return { x: Math.floor(this.width / 2), y: Math.floor(this.height / 2), dir: Direction.UP };
  }

  private clearGrid() {
    this.grid.fill(0);
    this.buffer.fill(0);
    this.metrics = { generation: 0, population: 0 };
    this.ant = this.createDefaultAnt();
  }

  public setRule(rule: AutomataRule) {
    this.rule = rule;
    this.clearGrid();
    return this.getFullGridUpdate();
  }

  public loadPreset(preset: Preset) {
    this.clearGrid();
    const offsetX = Math.floor(this.width / 2) - 8;
    const offsetY = Math.floor(this.height / 2) - 8;

    for (const point of preset.pattern) {
      // Cap dimensions to prevent out-of-bounds from malicious presets
      const x = Math.min(this.width - 1, point.x + offsetX);
      const y = Math.min(this.height - 1, point.y + offsetY);
      if (x >= 0 && y >= 0) {
        const index = y * this.width + x;
        this.grid[index] = 1;
      }
    }
    this.buffer.set(this.grid);
    return this.getFullGridUpdate();
  }

  public drawPoints(points: Point[]) {
    const changedCells: { x: number; y: number; state: number }[] = [];
    for (const { x, y } of points) {
      if (x >= 0 && x < this.width && y >= 0 && y < this.height) {
        const index = y * this.width + x;
        const currentState = this.grid[index];
        const newState = currentState === 0 ? 1 : 0;
        this.grid[index] = newState;
        this.buffer[index] = newState;
        changedCells.push({ x, y, state: newState });
      }
    }
    return changedCells;
  }

  private getFullGridUpdate() {
    const changedCells = [];
    let population = 0;
    for (let i = 0; i < this.grid.length; i++) {
      const state = this.grid[i];
      if (state === 1) population++;
      changedCells.push({ x: i % this.width, y: Math.floor(i / this.width), state });
    }
    this.metrics.population = population;
    return changedCells;
  }

  public step() {
    let result;
    if (this.rule === 'game-of-life') {
      result = stepGameOfLife(this.width, this.height, this.grid, this.buffer);
      this.grid.set(this.buffer);
    } else if (this.rule === 'langtons-ant') {
      // Langton's Ant modifies the grid in place
      result = stepLangtonsAnt(this.width, this.height, this.grid, this.ant);
    } else if (this.rule === 'rule-110') {
      // Rule 110 writes to the next line based on the current one
      result = stepRule110(this.width, this.height, this.grid, this.grid, this.metrics.generation);
    }

    if (result) {
      this.metrics.generation++;
      this.metrics.population = result.population;
      return result.changedCells;
    }
    return [];
  }
}
