import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import App from './App';
import { calculateCartTotals, formatCOP } from './utils/formatters';

describe('Aztec Colombian POS & Accounting App', () => {
  it('renders header, role switcher and POS catalog', () => {
    render(<App />);
    expect(screen.getByText(/Aztec POS & Contabilidad/i)).toBeInTheDocument();
    expect(screen.getByText(/Colombia DIAN/i)).toBeInTheDocument();
    expect(screen.getByText(/Café Juan Valdez 500g/i)).toBeInTheDocument();
    expect(screen.getByText(/Ticket de Venta POS/i)).toBeInTheDocument();
  });

  it('switches navigation tabs and shows ledger journal', () => {
    render(<App />);
    const ledgerTab = screen.getByText(/Libro Diario/i);
    fireEvent.click(ledgerTab);
    expect(screen.getByText(/Libro Diario & Mayor \(Partida Doble\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Balance Cuadrado/i)).toBeInTheDocument();
  });

  it('calculates Colombian IVA 19% correctly', () => {
    const mockItems = [
      { product: { price: 11900, ivaRate: 0.19 }, quantity: 1 },
      { product: { price: 5000, ivaRate: 0.00 }, quantity: 1 },
    ];
    const totals = calculateCartTotals(mockItems);
    expect(totals.total).toBe(16900);
    expect(totals.subtotal).toBe(15000);
    expect(totals.iva).toBe(1900);
  });
});
