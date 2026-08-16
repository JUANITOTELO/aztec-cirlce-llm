import React, { useRef, useEffect, useCallback } from 'react';
import { useResizeObserver } from '../hooks/useResizeObserver';
import { useCanvasInput } from '../hooks/useCanvasInput';
import { Point } from '../types/simulation';
import { CELL_COLOR, GRID_COLOR } from '../constants/config';

interface SimulationCanvasProps {
  width: number;
  height: number;
  onDraw: (points: Point[]) => void;
}

export const SimulationCanvas: React.FC<SimulationCanvasProps> = ({ width, height, onDraw }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageDataRef = useRef<ImageData | null>(null);
  const dimensions = useResizeObserver(containerRef);

  const drawHandler = useCallback((points: Point[]) => {
    onDraw(points);
  }, [onDraw]);

  useCanvasInput(canvasRef, width, height, drawHandler);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Initialize ImageData buffer
    imageDataRef.current = ctx.createImageData(width, height);
    // Initial clear
    ctx.fillStyle = GRID_COLOR;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }, [width, height]);

  useEffect(() => {
    const handleUpdate = (event: MessageEvent) => {
      if (event.data.type !== 'update') return;
      const { changedCells } = event.data;
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      const imageData = imageDataRef.current;

      if (!canvas || !ctx || !imageData || !changedCells) return;

      const data = imageData.data;
      for (const { x, y, state } of changedCells) {
        const i = (y * width + x) * 4;
        const color = state === 1 ? CELL_COLOR : GRID_COLOR;
        const [r, g, b] = color.match(/\w\w/g)!.map((hex) => parseInt(hex, 16));
        data[i] = r;
        data[i + 1] = g;
        data[i + 2] = b;
        data[i + 3] = 255; // Alpha
      }

      // Perform a single batched draw operation
      ctx.putImageData(imageData, 0, 0);
    };

    // This assumes the worker is instantiated elsewhere and listens globally
    // A more robust solution might use a dedicated event bus or context
    const worker = (window as any).simulationWorker;
    if (worker) {
      worker.addEventListener('message', handleUpdate);
    }

    return () => {
      if (worker) {
        worker.removeEventListener('message', handleUpdate);
      }
    };
  }, [width, height]);

  return (
    <div ref={containerRef} className="w-full h-full flex items-center justify-center">
      <canvas
        ref={canvasRef}
        width={dimensions?.width || width}
        height={dimensions?.height || height}
        className="bg-gray-900 object-contain"
      />
    </div>
  );
};
