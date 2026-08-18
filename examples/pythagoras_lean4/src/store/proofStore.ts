import { ProofAppState, GeometryParams, DissectionMode, TheoremType } from '../types/proofState';
import { validateGeometry } from '../engine/geometryEngine';
import { LeanKernelSimulator } from '../engine/leanKernelSimulator';
import { computeMerkleRoot } from '../utils/cryptoHash';

type Listener = (state: ProofAppState) => void;

class ProofStore {
  private state: ProofAppState;
  private listeners: Set<Listener> = new Set();

  constructor() {
    const initialParams = validateGeometry(6, 8, 'pythagoras');
    const tactics = LeanKernelSimulator.generateTactics(initialParams, 'pythagoras');
    const initialChecksum = computeMerkleRoot(tactics.map(t => t.merkleHash));

    this.state = {
      activeTheorem: 'pythagoras',
      params: initialParams,
      mode: 'zhoubi_suanjing',
      activeStepIndex: 0,
      isPlaying: false,
      playbackSpeed: 1,
      showImplicits: false,
      verifiedChecksum: initialChecksum
    };
  }

  public getState(): ProofAppState {
    return this.state;
  }

  public subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(): void {
    this.listeners.forEach(listener => listener(this.state));
  }

  public setTheorem(theorem: TheoremType): void {
    const defaultParams = theorem === 'pythagoras'
      ? validateGeometry(6, 8, 'pythagoras')
      : validateGeometry(5, 3, 'binomial');
    const tactics = LeanKernelSimulator.generateTactics(defaultParams, theorem);
    const checksum = computeMerkleRoot(tactics.map(t => t.merkleHash));

    this.state = {
      ...this.state,
      activeTheorem: theorem,
      params: defaultParams,
      mode: theorem === 'binomial' ? 'diagonal_slice' : 'zhoubi_suanjing',
      activeStepIndex: 0,
      isPlaying: false,
      verifiedChecksum: checksum
    };
    this.notify();
  }

  public setGeometry(a: number, b: number): void {
    const params = validateGeometry(a, b, this.state.activeTheorem);
    if (params.isValid) {
      const tactics = LeanKernelSimulator.generateTactics(params, this.state.activeTheorem);
      const checksum = computeMerkleRoot(tactics.map(t => t.merkleHash));
      this.state = { ...this.state, params, verifiedChecksum: checksum };
      this.notify();
    }
  }

  public setStepIndex(stepIndex: number): void {
    const tactics = LeanKernelSimulator.generateTactics(this.state.params, this.state.activeTheorem);
    const clampedIndex = Math.max(0, Math.min(stepIndex, tactics.length - 1));
    this.state = { ...this.state, activeStepIndex: clampedIndex };
    this.notify();
  }

  public setMode(mode: DissectionMode): void {
    this.state = { ...this.state, mode };
    this.notify();
  }

  public togglePlaying(): void {
    this.state = { ...this.state, isPlaying: !this.state.isPlaying };
    this.notify();
  }

  public setPlaybackSpeed(playbackSpeed: number): void {
    this.state = { ...this.state, playbackSpeed };
    this.notify();
  }

  public setShowImplicits(showImplicits: boolean): void {
    this.state = { ...this.state, showImplicits };
    this.notify();
  }
}

export const proofStore = new ProofStore();
