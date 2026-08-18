import { Point } from '../types/simulation';

/**
 * Converts screen coordinates (e.g., from a mouse click) to integer-based
 * grid coordinates, mitigating floating-point precision issues.
 */
export function screenToGridCoords(
  screenX: number,
  screenY: number,
  canvasRect: DOMRect,
  gridWidth: number,
  gridHeight: number,
): Point | null {
  const canvasX = screenX - canvasRect.left;
  const canvasY = screenY - canvasRect.top;

  // Handle cases where canvas is scaled to fit container
  const scaleX = canvasRect.width / gridWidth;
  const scaleY = canvasRect.height / gridHeight;

  const gridX = Math.floor(canvasX / scaleX);
  const gridY = Math.floor(canvasY / scaleY);

  if (gridX >= 0 && gridX < gridWidth && gridY >= 0 && gridY < gridHeight) {
    return { x: gridX, y: gridY };
  }

  return null;
}
