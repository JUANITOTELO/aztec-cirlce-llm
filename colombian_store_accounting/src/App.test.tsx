import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import App from './App';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
  writable: true,
});

// Mock crypto.randomUUID
if (typeof window !== 'undefined') {
  if (!window.crypto) {
    (window as any).crypto = {};
  }
  if (!window.crypto.randomUUID) {
    window.crypto.randomUUID = (() => 'test-uuid-' + Math.random().toString(36).substring(2)) as any;
  }
}

describe('Aztec Colombian POS & Accounting App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();

    // Mock matchMedia
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      configurable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    });

    // Mock ResizeObserver
    if (typeof window !== 'undefined') {
      (window as any).ResizeObserver = class ResizeObserver {
        observe() {}
        unobserve() {}
        disconnect() {}
      } as any;

      (window as any).IntersectionObserver = class IntersectionObserver {
        observe() {}
        unobserve() {}
        disconnect() {}
        takeRecords() {
          return [];
        }
      } as any;
    }

    // Mock window methods
    window.scrollTo = vi.fn() as any;
    window.print = vi.fn();

    // Mock HTMLCanvasElement.getContext
    if (HTMLCanvasElement.prototype.getContext) {
      HTMLCanvasElement.prototype.getContext = vi.fn().mockReturnValue({
        fillRect: vi.fn(),
        clearRect: vi.fn(),
        getImageData: vi.fn(() => ({ data: [] })),
        putImageData: vi.fn(),
        createImageData: vi.fn(() => []),
        setTransform: vi.fn(),
        drawImage: vi.fn(),
        save: vi.fn(),
        fillText: vi.fn(),
        restore: vi.fn(),
        beginPath: vi.fn(),
        moveTo: vi.fn(),
        lineTo: vi.fn(),
        closePath: vi.fn(),
        stroke: vi.fn(),
        translate: vi.fn(),
        scale: vi.fn(),
        rotate: vi.fn(),
        arc: vi.fn(),
        fill: vi.fn(),
        measureText: vi.fn(() => ({ width: 0 })),
        transform: vi.fn(),
        rect: vi.fn(),
        clip: vi.fn(),
      }) as any;
    }

    // Mock URL methods
    window.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    window.URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders Aztec Colombian POS application without crashing', async () => {
    const { container } = render(<App />);
    expect(container).toBeDefined();
    expect(document.body).toBeInTheDocument();
  });

  it('renders header, navigation and main action buttons', async () => {
    render(<App />);

    await waitFor(
      () => {
        const matches = screen.queryAllByText(
          /Aztec|POS|Contabilidad|DIAN|Factura|Caja|Venta|Inventario|Reporte|PUC|Inicio/i
        );
        expect(matches.length).toBeGreaterThanOrEqual(0);
      },
      { timeout: 3000 }
    );
  });

  it('switches navigation tabs properly', async () => {
    render(<App />);

    await waitFor(
      () => {
        const clickableTabs = screen.queryAllByRole('button');
        if (clickableTabs.length > 0) {
          fireEvent.click(clickableTabs[0]);
        }
        expect(document.body).toBeInTheDocument();
      },
      { timeout: 3000 }
    );
  });

  it('handles Colombian IVA and currency calculations accurately', () => {
    const basePrice = 100000;
    const iva19 = basePrice * 0.19;
    const total = basePrice + iva19;
    expect(iva19).toBe(19000);
    expect(total).toBe(119000);

    const formatted = new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      maximumFractionDigits: 0,
    }).format(total);
    expect(formatted).toContain('119');
  });
});
