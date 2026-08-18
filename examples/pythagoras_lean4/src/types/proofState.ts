export type TheoremType = 'pythagoras' | 'binomial' | 'gougu';

export type DissectionMode = 'rearrangement' | 'zhoubi_suanjing' | 'diagonal_slice' | 'xian_tu';

export interface GeometryParams {
  readonly a: number;
  readonly b: number;
  readonly c?: number;
  readonly isValid: boolean;
  readonly validationError?: string;
}

export interface ProofAppState {
  readonly activeTheorem: TheoremType;
  readonly params: GeometryParams;
  readonly mode: DissectionMode;
  readonly activeStepIndex: number;
  readonly isPlaying: boolean;
  readonly playbackSpeed: number;
  readonly showImplicits: boolean;
  readonly verifiedChecksum: string;
}
