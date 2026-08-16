import { useState, useEffect, RefObject } from 'react';

export function useResizeObserver(ref: RefObject<Element>) {
  const [dimensions, setDimensions] = useState<{ width: number; height: number } | null>(null);

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new ResizeObserver(entries => {
      if (entries[0]) {
        const { width, height } = entries[0].contentRect;
        setDimensions({ width, height });
      }
    });

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [ref]);

  return dimensions;
}
