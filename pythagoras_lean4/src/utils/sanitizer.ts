export function sanitizeNumber(val: number, fallback = 0): number {
  if (!Number.isFinite(val) || Number.isNaN(val)) return fallback;
  return Math.max(0.0001, Math.min(val, 10000));
}

export function pointsToSvgPath(points: readonly { x: number; y: number }[]): string {
  if (!points || points.length === 0) return '';
  const start = `M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`;
  const lines = points.slice(1).map(p => `L ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ');
  return `${start} ${lines} Z`;
}