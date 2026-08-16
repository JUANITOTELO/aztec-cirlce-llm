import { RefObject, useEffect, useRef } from 'react';
import { Point } from '../types/simulation';
import { screenToGridCoords } from '../utils/geometry';

export function useCanvasInput(
  canvasRef: RefObject<HTMLCanvasElement>,
  gridWidth: number,
  gridHeight: number,
  onDraw: (points: Point[]) => void,
) {
  const isDrawingRef = useRef(false);
  const drawnPointsRef = useRef<Point[]>([]);
  const lastPointRef = useRef<Point | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const addPoint = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      const newPoint = screenToGridCoords(e.clientX, e.clientY, rect, gridWidth, gridHeight);
      if (!newPoint) return;

      const lastPoint = lastPointRef.current;
      if (!lastPoint || lastPoint.x !== newPoint.x || lastPoint.y !== newPoint.y) {
        drawnPointsRef.current.push(newPoint);
        lastPointRef.current = newPoint;
      }
    };

    const handlePointerDown = (e: PointerEvent) => {
      if (e.button !== 0 || e.altKey || e.shiftKey) return;
      isDrawingRef.current = true;
      addPoint(e);
    };

    const handlePointerMove = (e: PointerEvent) => {
      if (!isDrawingRef.current) return;
      addPoint(e);
    };

    const handlePointerUp = () => {
      isDrawingRef.current = false;
      lastPointRef.current = null;
    };

    const flushDrawBuffer = () => {
      if (drawnPointsRef.current.length > 0) {
        onDraw(drawnPointsRef.current);
        drawnPointsRef.current = [];
      }
      requestAnimationFrame(flushDrawBuffer);
    };

    canvas.addEventListener('pointerdown', handlePointerDown);
    canvas.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
    const rafId = requestAnimationFrame(flushDrawBuffer);

    return () => {
      canvas.removeEventListener('pointerdown', handlePointerDown);
      canvas.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
      cancelAnimationFrame(rafId);
    };
  }, [canvasRef, gridWidth, gridHeight, onDraw]);
}
