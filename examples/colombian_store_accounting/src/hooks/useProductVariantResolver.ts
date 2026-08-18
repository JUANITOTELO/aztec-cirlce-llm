import { useCallback } from 'react';
import { Product } from '../types/store';
import { ProductVariant } from '../types/productVariant';

export interface ResolvedVariantResult {
  product: Product;
  variant: ProductVariant;
  unitPrice: number;
  unitCost: number;
}

export function useProductVariantResolver(products: Product[], variants: ProductVariant[]) {
  const resolveByBarcode = useCallback((barcode: string): ResolvedVariantResult | null => {
    const clean = barcode.trim();
    const variant = variants.find((v) => v.barcode === clean && v.isActive);
    if (variant) {
      const prod = products.find((p) => p.id === variant.productId);
      if (prod) {
        return {
          product: prod,
          variant,
          unitPrice: variant.price,
          unitCost: variant.cost,
        };
      }
    }
    const prod = products.find((p) => p.barcode === clean);
    if (prod) {
      const defVariant = variants.find((v) => v.productId === prod.id && v.isDefault) ||
        variants.find((v) => v.productId === prod.id);
      if (defVariant) {
        return {
          product: prod,
          variant: defVariant,
          unitPrice: defVariant.price,
          unitCost: defVariant.cost,
        };
      }
    }
    return null;
  }, [products, variants]);

  const getVariantsForProduct = useCallback((productId: string): ProductVariant[] => {
    return variants.filter((v) => v.productId === productId && v.isActive);
  }, [variants]);

  return { resolveByBarcode, getVariantsForProduct };
}