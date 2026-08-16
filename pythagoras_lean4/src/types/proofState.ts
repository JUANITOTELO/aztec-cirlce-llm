export type DissectionMode = 'rearrangement' | 'zhoubi_suanjing';

export interface GeometryParams {
  readonly a: number;
  readonly b: number;
  readonly c: number;
  readonly isValid: boolean;
  readonly validationError?: string;
}

export interface ProofAppState {
  readonly params: GeometryParams;
  readonly mode: DissectionMode;
  readonly activeStepIndex: number;
  readonly isPlaying: boolean;
  readonly playbackSpeed: number;
  readonly showImplicits: boolean;
  readonly verifiedChecksum: string;
}