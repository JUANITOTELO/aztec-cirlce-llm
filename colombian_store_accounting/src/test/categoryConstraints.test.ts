import { describe, it, expect } from 'vitest';
import { sanitizeCategoryText, validateCategoryPayload, checkOrphanProducts, reassignProductsToCategory, resolveLedgerAccount } from '../engine/categoryConstraints';
import { INITIAL_CATEGORIES } from '../constants/mockCategories';
import { Product } from '../types/store';

describe('Category Domain Constraints & Engine', () => {
  it('sanitizes unsafe category names correctly', () => {
    const malicious = '<script>alert(1)</script> Lácteos & Más "\'';
    const clean = sanitizeCategoryText(malicious);
    expect(clean).toBe('scriptalert(1)script Lácteos & Más');
    expect(clean).not.toContain('<');
    expect(clean).not.toContain('>');
  });

  it('validates category mutation payloads with PUC validation', () => {
    const valid = validateCategoryPayload({
      name: 'Bebidas Artesanales',
      color: '#3B82F6',
      ledgerAccountCode: '413510',
    });
    expect(valid.valid).toBe(true);

    const invalid = validateCategoryPayload({
      name: '',
      color: 'not-a-color',
      ledgerAccountCode: 'ABC',
    });
    expect(invalid.valid).toBe(false);
    expect(invalid.errors.length).toBeGreaterThanOrEqual(3);
  });

  it('detects orphan products when categories are deleted', () => {
    const sampleProducts: Product[] = [
      { id: '1', name: 'Arroz', sku: 'AR-1', category: 'Abarrotes', price: 1000, cost: 800, stock: 10, minStock: 2, ivaRate: 0, barcode: '111' },
      { id: '2', name: 'Vino', sku: 'VN-1', category: 'Licores Inexistentes', price: 50000, cost: 30000, stock: 4, minStock: 1, ivaRate: 0.19, barcode: '222' },
    ];

    const report = checkOrphanProducts(sampleProducts, INITIAL_CATEGORIES);
    expect(report.hasOrphans).toBe(true);
    expect(report.orphanProductCount).toBe(1);
    expect(report.orphanProductIds).toContain('2');
  });

  it('reassigns products atomically between categories', () => {
    const sampleProducts: Product[] = [
      { id: '1', name: 'Galleta', sku: 'GL-1', category: 'Snacks', price: 1000, cost: 700, stock: 5, minStock: 1, ivaRate: 0.19, barcode: '123' },
    ];
    const reassigned = reassignProductsToCategory(sampleProducts, 'Snacks', 'Abarrotes');
    expect(reassigned[0].category).toBe('Abarrotes');
  });

  it('resolves correct Colombian PUC revenue accounts', () => {
    const account = resolveLedgerAccount('Abarrotes', INITIAL_CATEGORIES);
    expect(account.code).toBe('413505');
    expect(account.name).toContain('Alimentos');

    const fallback = resolveLedgerAccount('Categoria Desconocida', INITIAL_CATEGORIES);
    expect(fallback.code).toBe('413595');
  });
});