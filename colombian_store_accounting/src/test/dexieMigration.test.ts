import { describe, it, expect } from 'vitest';
import { db, deleteProductWithCascade } from '../db/dexie';

describe('Dexie IndexedDB and Cascade Operations', () => {
  it('instantiates all required tables including variantAuditLogs', () => {
    expect(db.productVariants).toBeDefined();
    expect(db.productImages).toBeDefined();
    expect(db.variantAuditLogs).toBeDefined();
    expect(db.categories).toBeDefined();
  });

  it('performs cascade deletion when a product is removed', async () => {
    const testProdId = 'prod-test-cascade';
    await db.productVariants.put({
      id: 'var-test',
      productId: testProdId,
      sku: 'TEST-SKU',
      name: 'Test Variant',
      attributes: {},
      price: 100,
      cost: 50,
      stock: 1,
      minStock: 0,
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    });
    await db.productImages.put({
      id: 'img-test',
      productId: testProdId,
      url: 'http://example.com/test.png',
      fileName: 'test.png',
      fileSize: 100,
      mimeType: 'image/png',
      isPrimary: true,
      order: 0,
      createdAt: new Date().toISOString()
    });
    await db.variantAuditLogs.put({
      id: 'audit-test',
      variantId: 'var-test',
      productId: testProdId,
      action: 'CREATE',
      timestamp: new Date().toISOString(),
      userId: 'usr-1',
      changes: {}
    });

    await deleteProductWithCascade(testProdId);

    const remainingVariants = await db.productVariants.where('productId').equals(testProdId).toArray();
    const remainingImages = await db.productImages.where('productId').equals(testProdId).toArray();
    const remainingAudit = await db.variantAuditLogs.where('productId').equals(testProdId).toArray();

    expect(remainingVariants.length).toBe(0);
    expect(remainingImages.length).toBe(0);
    expect(remainingAudit.length).toBe(0);
  });
});
