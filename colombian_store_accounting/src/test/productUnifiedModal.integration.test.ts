import { describe, it, expect } from 'vitest';
import { sanitizeVariantSku, sanitizeVariantName } from '../engine/variantSanitization';
import { INITIAL_PRODUCTS } from '../constants/mockData';
import { INITIAL_CATEGORIES } from '../constants/mockCategories';
import { INITIAL_VARIANTS, INITIAL_PRODUCT_IMAGES } from '../constants/mockVariants';

describe('Product Unified Modal & Sync Verification', () => {
  it('sanitizes variant and product inputs correctly', () => {
    const dirtySku = '  ab-001-xyz  ';
    const dirtyName = '  Café & Organic   ';
    expect(sanitizeVariantSku(dirtySku)).toBe('AB-001-XYZ');
    expect(sanitizeVariantName(dirtyName)).toBe('Café & Organic');
  });

  it('verifies initial products link properly to mock variants and images', () => {
    const product1 = INITIAL_PRODUCTS[0];
    const product1Variants = INITIAL_VARIANTS.filter((v) => v.productId === product1.id);
    const product1Images = INITIAL_PRODUCT_IMAGES.filter((img) => img.productId === product1.id);

    expect(product1Variants.length).toBeGreaterThan(0);
    expect(product1Images.length).toBeGreaterThan(0);
    expect(product1Variants[0].sku).toContain(product1.sku);
  });

  it('ensures product category matches catalog categories', () => {
    const validCatNames = INITIAL_CATEGORIES.map((c) => c.name);
    for (const prod of INITIAL_PRODUCTS) {
      expect(validCatNames).toContain(prod.category);
    }
  });
});
