import React, { useRef, useEffect, useCallback } from 'react';
import { useCanvasInput } from '../hooks/useCanvasInput';
import { useCanvasPan } from '../hooks/useCanvasPan';
import { Point } from '../types/simulation';
import { CELL_COLOR, GRID_COLOR } from '../constants/config';

interface SimulationCanvasProps {
  width: number;
  height: number;
  onDraw: (points: Point[]) => void;
  worker?: Worker | null;
}

export const SimulationCanvas: React.FC<SimulationCanvasProps> = ({ width, height, onDraw, worker }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageDataRef = useRef<ImageData | null>(null);
  const { pan, zoom } = useCanvasPan(containerRef);

  const drawHandler = useCallback((points: Point[]) => {
    onDraw(points);
  }, [onDraw]);

  useCanvasInput(canvasRef, width, height, drawHandler);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    imageDataRef.current = ctx.createImageData(width, height);
    const data = imageDataRef.current.data;
    const [gr, gg, gb] = GRID_COLOR.match(/\w\w/g)!.map((hex) => parseInt(hex, 16));
    for (let i = 0; i < data.length; i += 4) {
      data[i] = gr;
      data[i + 1] = gg;
      data[i + 2] = gb;
      data[i + 3] = 255;
    }
    ctx.putImageData(imageDataRef.current, 0, 0);
  }, [width, height]);

  useEffect(() => {
    const targetWorker = worker || (window as any).simulationWorker;
    if (!targetWorker) return;

    const [cr, cg, cb] = CELL_COLOR.match(/\w\w/g)!.map((hex) => parseInt(hex, 16));
    const [gr, gg, gb] = GRID_COLOR.match(/\w\w/g)!.map((hex) => parseInt(hex, 16));

    const handleUpdate = (event: MessageEvent) => {
      if (event.data?.type !== 'update') return;
      const { changedCells } = event.data;
      const canvas = canvasRef.current;
      const ctx = canvas?.getContext('2d');
      const imageData = imageDataRef.current;

      if (!canvas || !ctx || !imageData || !changedCells) return;

      const data = imageData.data;
      for (const { x, y, state } of changedCells) {
        if (x < 0 || x >= width || y < 0 || y >= height) continue;
        const index = (y * width + x) * 4;
        if (state) {
          data[index] = cr;
          data[index + 1] = cg;
          data[index + 2] = cb;
          data[index + 3] = 255;
        } else {
          data[index] = gr;
          data[index + 1] = gg;
          data[index + 2] = gb;
          data[index + 3] = 255;
        }
      }
      ctx.putImageData(imageData, 0, 0);
    };

    targetWorker.addEventListener('message', handleUpdate);
    return () => {
      targetWorker.removeEventListener('message', handleUpdate);
    };
  }, [width, height, worker]);

  return (
    <div ref={containerRef} className="w-full h-full flex items-center justify-center p-4 box-border overflow-hidden select-none">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="shadow-2xl border border-gray-700 cursor-crosshair touch-none"
        style={{
          imageRendering: 'pixelated',
          aspectRatio: `${width} / ${height}`,
          width: 'auto',
          height: '100%',
          maxWidth: '100%',
          maxHeight: '100%',
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: 'center center',
        }}
      />
    </div>
  );
};
