import { useState, useEffect, useRef, RefObject } from 'react';

export function useCanvasPan(containerRef: RefObject<HTMLElement>) {
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const panRef = useRef(pan);
  panRef.current = pan;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    let isPanning = false;
    let startX = 0;
    let startY = 0;

    const handlePointerDown = (e: PointerEvent) => {
      if (e.button === 1 || e.button === 2 || (e.button === 0 && (e.altKey || e.shiftKey))) {
        isPanning = true;
        startX = e.clientX - panRef.current.x;
        startY = e.clientY - panRef.current.y;
      }
    };

    const handlePointerMove = (e: PointerEvent) => {
      if (!isPanning) return;
      setPan({ x: e.clientX - startX, y: e.clientY - startY });
    };

    const handlePointerUp = () => {
      isPanning = false;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      if (e.ctrlKey || e.metaKey) {
        const factor = e.deltaY < 0 ? 1.1 : 0.9;
        setZoom((prev) => Math.min(Math.max(prev * factor, 0.1), 20));
      } else {
        setPan((prev) => ({ x: prev.x - e.deltaX, y: prev.y - e.deltaY }));
      }
    };

    const handleContextMenu = (e: MouseEvent) => e.preventDefault();

    el.addEventListener('pointerdown', handlePointerDown);
    window.addEventListener('pointermove', handlePointerMove);
    window.addEventListener('pointerup', handlePointerUp);
    el.addEventListener('wheel', handleWheel, { passive: false });
    el.addEventListener('contextmenu', handleContextMenu);

    return () => {
      el.removeEventListener('pointerdown', handlePointerDown);
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
      el.removeEventListener('wheel', handleWheel);
      el.removeEventListener('contextmenu', handleContextMenu);
    };
  }, [containerRef]);

  return { pan, zoom, setZoom, setPan };
}
