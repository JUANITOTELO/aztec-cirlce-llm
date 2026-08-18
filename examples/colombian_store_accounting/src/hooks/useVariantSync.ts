import { useEffect, useCallback } from 'react';
import { ProductVariant } from '../types/productVariant';
import { db } from '../db/dexie';
import { sanitizeVariantSku, sanitizeVariantName } from '../engine/variantSanitization';

export interface UseVariantSyncReturn {
  persistVariantMutation: (variant: ProductVariant) => Promise<void>;
  deleteVariant: (variantId: string) => Promise<void>;
  refreshVariants: (productId: string) => Promise<ProductVariant[]>;
}

export function useVariantSync(
  variants: ProductVariant[],
  setVariants: React.Dispatch<React.SetStateAction<ProductVariant[]>>
): UseVariantSyncReturn {
  const persistVariantMutation = useCallback(
    async (variant: ProductVariant): Promise<void> => {
      try {
        const sanitized: ProductVariant = {
          ...variant,
          name: sanitizeVariantName(variant.name),
          sku: sanitizeVariantSku(variant.sku),
          updatedAt: new Date().toISOString(),
        };
        await db.productVariants.put(sanitized);
        setVariants((prev) => {
          const exists = prev.some((v) => v.id === sanitized.id);
          if (exists) {
            return prev.map((v) => (v.id === sanitized.id ? sanitized : v));
          }
          return [...prev, sanitized];
        });
      } catch (err) {
        console.error('Failed to persist variant mutation:', err);
        throw err;
      }
    },
    [setVariants]
  );

  const deleteVariant = useCallback(
    async (variantId: string): Promise<void> => {
      try {
        await db.productVariants.delete(variantId);
        await db.productImages.where('variantId').equals(variantId).delete();
        setVariants((prev) => prev.filter((v) => v.id !== variantId));
      } catch (err) {
        console.error('Failed to delete variant:', err);
        throw err;
      }
    },
    [setVariants]
  );

  const refreshVariants = useCallback(
    async (productId: string): Promise<ProductVariant[]> => {
      try {
        const list = await db.productVariants.where('productId').equals(productId).toArray();
        return list;
      } catch (err) {
        console.error('Failed to refresh variants:', err);
        return variants.filter((v) => v.productId === productId);
      }
    },
    [variants]
  );

  return {
    persistVariantMutation,
    deleteVariant,
    refreshVariants,
  };
}
