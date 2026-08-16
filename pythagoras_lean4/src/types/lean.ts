export type ProofStatus = 'PROVEN' | 'IN_PROGRESS' | 'UNPROVEN' | 'FAILED';

export interface LeanHypothesis {
  readonly id: string;
  readonly name: string;
  readonly type: string;
  readonly value?: string;
  readonly isImplicit?: boolean;
}

export interface LeanTacticState {
  readonly stepIndex: number;
  readonly tacticApplied: string;
  readonly hypotheses: readonly LeanHypothesis[];
  readonly goals: readonly string[];
  readonly status: ProofStatus;
  readonly merkleHash: string;
  readonly logicalClock: number;
  readonly explanation: string;
}

export interface LeanProjectExport {
  readonly lakefile: string;
  readonly leanSource: string;
  readonly toolchain: string;
  readonly verificationHash: string;
  readonly timestamp: string;
}