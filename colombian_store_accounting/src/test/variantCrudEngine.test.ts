import { describe, it, expect } from 'vitest';
import { validateVariantPayload, buildNewVariant, buildNewImage, generateUUID } from '../engine/variantCrudEngine';
import { ProductVariant } from '../types/productVariant';

describe('variantCrudEngine', () => {
  it('generates a valid UUID string', () => {
    const uuid = generateUUID();
    expect(uuid).toBeDefined();
    expect(uuid.length).toBe(36);
  });

  it('validates variant payload with missing name and SKU', () => {
    const result = validateVariantPayload({ name: '', sku: '', price: -10, cost: 0, stock: 0, minStock: 0, isActive: true, attributes: {} }, []);
    expect(result.isValid).toBe(false);
    expect(result.errors.name).toBeDefined();
    expect(result.errors.sku).toBeDefined();
    expect(result.errors.price).toBeDefined();
  });

  it('detects duplicate SKUs', () => {
    const existing: ProductVariant[] = [
      { id: 'v1', productId: 'p1', sku: 'SKU-100', name: 'Var 1', attributes: {}, price: 1000, cost: 500, stock: 10, minStock: 2, isActive: true, createdAt: '', updatedAt: '' }
    ];
    const result = validateVariantPayload({ name: 'Var 2', sku: 'sku-100', price: 1000, cost: 500, stock: 10, minStock: 2, isActive: true, attributes: {} }, existing);
    expect(result.isValid).toBe(false);
    expect(result.errors.sku).toContain('ya se encuentra registrado');
  });

  it('builds a new sanitized variant object', () => {
    const variant = buildNewVariant('prod-1', {
      name: '  Camisa Roja  ', sku: 'cr-01', price: 50000, cost: 30000, stock: 5, minStock: 1, isActive: true, attributes: { Color: 'Rojo' }
    });
    expect(variant.productId).toBe('prod-1');
    expect(variant.name).toBe('Camisa Roja');
    expect(variant.sku).toBe('CR-01');
    expect(variant.attributes.Color).toBe('Rojo');
    expect(variant.id).toMatch(/^var-/);
  });

  it('builds a new product image metadata record', () => {
    const img = buildNewImage('prod-1', 'data:image/png;base64,123', 'foto.png', 1024, 'image/png', undefined, true, 0);
    expect(img.productId).toBe('prod-1');
    expect(img.isPrimary).toBe(true);
    expect(img.mimeType).toBe('image/png');
    expect(img.id).toMatch(/^img-/);
  });
});
