import { describe, it, expect, beforeEach } from 'vitest';
import { sanitizeVariantName, sanitizeVariantSku, sanitizeAttributes } from '../engine/variantSanitization';
import { createVariantAuditEntry } from '../engine/variantAuditLogger';

describe('Product Variant Sanitization & Engine Logic', () => {
  it('sanitizes variant name removing dangerous script tags', () => {
    const raw = '<script>alert(1)</script>Café Molido Premium;';
    const cleaned = sanitizeVariantName(raw);
    expect(cleaned).not.toContain('<script>');
    expect(cleaned).toContain('Café Molido Premium');
  });

  it('sanitizes variant SKU to uppercase alphanumeric with hyphens', () => {
    const raw = 'ab-001/special!@#';
    const cleaned = sanitizeVariantSku(raw);
    expect(cleaned).toBe('AB-001SPECIAL');
  });

  it('sanitizes dynamic variant attributes cleanly', () => {
    const attrs = { size: '500g', color: 'Rojo <br>', flavor: 'Vainilla;' };
    const cleaned = sanitizeAttributes(attrs);
    expect(cleaned.size).toBe('500g');
    expect(cleaned.color).toBe('Rojo br');
  });

  it('computes deltas correctly in audit log creation', () => {
    const oldV = { price: 20000, stock: 10 };
    const newV = { price: 25000, stock: 10 };
    const log = createVariantAuditEntry('var-1', 'prod-1', 'UPDATED', 'usr-test', oldV, newV);
    expect(log.deltas?.price).toEqual({ old: 20000, new: 25000 });
    expect(log.deltas?.stock).toBeUndefined();
  });
});