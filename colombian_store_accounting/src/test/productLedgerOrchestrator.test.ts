import { describe, it, expect } from 'vitest';
import { ProductLedgerOrchestrator } from '../engine/productLedgerOrchestrator';
import { StockAdjustmentPayload } from '../types/product';
import { Product } from '../types/store';

describe('ProductLedgerOrchestrator', () => {
  const mockProduct: Product = {
    id: 'prod-test-1',
    sku: 'TEST-001',
    name: 'Café Test 500g',
    category: 'Abarrotes',
    price: 25000,
    cost: 15000,
    stock: 20,
    minStock: 5,
    ivaRate: 0.19,
    barcode: '7702001',
  };

  it('generates balanced double-entry entries for stock supplier addition (PUC 1435 vs 2205)', () => {
    const payload: StockAdjustmentPayload = {
      id: 'adj-01',
      productId: mockProduct.id,
      sku: mockProduct.sku,
      productName: mockProduct.name,
      adjustmentType: 'ADD',
      quantity: 10,
      unitCost: 15000,
      reason: 'COMPRA_PROVEEDOR',
      notes: 'Factura F-999',
      adjustedBy: 'Admin',
      adjustedAt: '2026-08-16T12:00:00Z',
    };

    const entries = ProductLedgerOrchestrator.emitStockAdjustment(payload);
    expect(entries).toHaveLength(2);

    const totalDebit = entries.reduce((s, e) => s + e.debit, 0);
    const totalCredit = entries.reduce((s, e) => s + e.credit, 0);
    expect(totalDebit).toBe(150000);
    expect(totalCredit).toBe(150000);
    expect(entries[0].pucCode).toBe('143501');
    expect(entries[1].pucCode).toBe('220505');
  });

  it('generates waste loss entries (PUC 5315 vs 1435) on inventory damage', () => {
    const payload: StockAdjustmentPayload = {
      id: 'adj-02',
      productId: mockProduct.id,
      sku: mockProduct.sku,
      productName: mockProduct.name,
      adjustmentType: 'REMOVE',
      quantity: 2,
      unitCost: 15000,
      reason: 'MERMA_DETERIORO',
      notes: 'Bolsa rota',
      adjustedBy: 'Contador',
      adjustedAt: '2026-08-16T12:00:00Z',
    };

    const entries = ProductLedgerOrchestrator.emitStockAdjustment(payload);
    expect(entries).toHaveLength(2);
    expect(entries[0].pucCode).toBe('531515');
    expect(entries[1].pucCode).toBe('143501');
    expect(entries[0].debit).toBe(30000);
    expect(entries[1].credit).toBe(30000);
  });

  it('creates immutable pricing audit record correctly', () => {
    const record = ProductLedgerOrchestrator.createPricingAuditRecord(
      mockProduct,
      { price: 28000, cost: 16000 },
      'Valentina',
      'Aumento costos proveedor'
    );

    expect(record.oldPrice).toBe(25000);
    expect(record.newPrice).toBe(28000);
    expect(record.oldCost).toBe(15000);
    expect(record.newCost).toBe(16000);
    expect(record.changedBy).toBe('Valentina');
  });
});
