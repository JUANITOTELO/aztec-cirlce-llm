export interface Point2D {
  readonly x: number;
  readonly y: number;
}

export interface TriangleShape {
  readonly id: number;
  readonly points: [Point2D, Point2D, Point2D];
  readonly color: string;
  readonly label: string;
}

export interface SquareShape {
  readonly id: string;
  readonly points: [Point2D, Point2D, Point2D, Point2D];
  readonly color: string;
  readonly label: string;
  readonly area: number;
}

export interface DissectionFrame {
  readonly triangles: readonly TriangleShape[];
  readonly squares: readonly SquareShape[];
  readonly outerDimension: number;
  readonly description: string;
  readonly proofStepIndex: number;
  readonly checksum: string;
}