import { describe, it, expect, beforeEach } from 'vitest';
import { db, deleteVariantWithCascade } from '../db/dexie';
import { INITIAL_PRODUCT_IMAGES, INITIAL_VARIANTS } from '../constants/mockVariants';

describe('MediaContext & Dexie Integration Suite', () => {
  beforeEach(async () => {
    await db.productImages.clear();
    await db.productVariants.clear();
    await db.productImages.bulkAdd(INITIAL_PRODUCT_IMAGES);
    await db.productVariants.bulkAdd(INITIAL_VARIANTS);
  });

  it('maintains images associated with products and variants in IndexedDB', async () => {
    const images = await db.productImages.where('productId').equals('prod-1').toArray();
    expect(images.length).toBeGreaterThan(0);
  });

  it('cascades deletion of variant images when variant is deleted', async () => {
    const targetVariantId = 'var-1-1';
    const beforeImages = await db.productImages.where('variantId').equals(targetVariantId).toArray();
    expect(beforeImages.length).toBeGreaterThanOrEqual(1);

    await deleteVariantWithCascade(targetVariantId);

    const afterImages = await db.productImages.where('variantId').equals(targetVariantId).toArray();
    expect(afterImages.length).toBe(0);
  });
});