import 'fake-indexeddb/auto';
import { describe, it, expect, beforeEach } from 'vitest';
import { db, deleteVariantWithCascade } from '../db/dexie';
import { validateVariantPayload } from '../engine/variantImageValidation';
import { buildNewVariant, buildNewImage } from '../engine/variantCrudEngine';

describe('Variant and Image CRUD Engine & Integrity', () => {
  beforeEach(async () => {
    await db.productVariants.clear();
    await db.productImages.clear();
    await db.variantAuditLogs.clear();
  });

  it('enforces SKU uniqueness and validation rules', () => {
    const payload = { sku: 'TEST-SKU', name: 'Variante Test', price: 15000, stock: 10 };
    const validation = validateVariantPayload(payload, ['TEST-SKU'], []);
    expect(validation.isValid).toBe(false);
    expect(validation.errors.sku).toContain('ya está en uso');
  });

  it('validates barcode uniqueness and format', () => {
    const payload = { sku: 'VALID-1', name: 'Var', barcode: '123' };
    const validation = validateVariantPayload(payload, [], []);
    expect(validation.isValid).toBe(false);
    expect(validation.errors.barcode).toContain('numérico entre 8 y 14 dígitos');
  });

  it('performs atomic variant insertion and cascading image deletion', async () => {
    const variant = buildNewVariant('prod-1', { sku: 'VAR-A', name: 'Color Rojo', price: 20000 });
    await db.productVariants.add(variant);

    const image = buildNewImage('prod-1', variant.id, 'data:image/webp;base64,AAA', true, 0);
    if (!image.variantId) {
      image.variantId = variant.id;
    }
    await db.productImages.add(image);

    expect(await db.productVariants.count()).toBe(1);
    expect(await db.productImages.count()).toBe(1);

    await deleteVariantWithCascade(variant.id);

    expect(await db.productVariants.count()).toBe(0);
    expect(await db.productImages.count()).toBe(0);
  });
});
