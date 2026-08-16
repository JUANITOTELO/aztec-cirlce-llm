import { ProofAppState, DissectionMode } from '../types/proofState';
import { LeanTacticState } from '../types/lean';
import { validateGeometry } from '../engine/geometryEngine';
import { LeanKernelSimulator } from '../engine/leanKernelSimulator';
import { DEFAULT_GEOMETRY } from '../constants/leanPresets';

type Listener = () => void;
const simulator = new LeanKernelSimulator();

class ProofStore {
  private state: ProofAppState = {
    params: validateGeometry(DEFAULT_GEOMETRY.a, DEFAULT_GEOMETRY.b),
    mode: 'zhoubi_suanjing',
    activeStepIndex: 0,
    isPlaying: false,
    playbackSpeed: 1,
    showImplicits: false,
    verifiedChecksum: ''
  };

  private tacticStates: readonly LeanTacticState[] = [];
  private listeners = new Set<Listener>();

  constructor() {
    this.recomputeTactics();
  }

  public getState = (): ProofAppState => this.state;
  public getTacticStates = (): readonly LeanTacticState[] => this.tacticStates;

  public subscribe = (listener: Listener): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  private notify() {
    this.listeners.forEach(l => l());
  }

  private recomputeTactics() {
    this.tacticStates = simulator.generateTacticSequence(this.state.params);
    this.state = {
      ...this.state,
      verifiedChecksum: this.tacticStates[this.tacticStates.length - 1]?.merkleHash || ''
    };
  }

  public setGeometry(a: number, b: number) {
    const params = validateGeometry(a, b);
    this.state = { ...this.state, params };
    this.recomputeTactics();
    this.notify();
  }

  public setStepIndex(idx: number) {
    const clamped = Math.max(0, Math.min(idx, this.tacticStates.length - 1));
    this.state = { ...this.state, activeStepIndex: clamped };
    this.notify();
  }

  public setMode(mode: DissectionMode) {
    this.state = { ...this.state, mode };
    this.notify();
  }

  public togglePlaying() {
    this.state = { ...this.state, isPlaying: !this.state.isPlaying };
    this.notify();
  }

  public setShowImplicits(show: boolean) {
    this.state = { ...this.state, showImplicits: show };
    this.notify();
  }

  public setPlaybackSpeed(speed: number) {
    this.state = { ...this.state, playbackSpeed: speed };
    this.notify();
  }
}

export const proofStore = new ProofStore();