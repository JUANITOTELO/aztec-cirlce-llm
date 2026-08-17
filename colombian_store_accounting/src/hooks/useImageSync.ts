import React, { useCallback } from 'react';
import { ProductImage } from '../types/productMedia';
import { db } from '../db/dexie';

export interface UseImageSyncReturn {
  persistImageMutation: (image: ProductImage) => Promise<void>;
  deleteImage: (imageId: string) => Promise<void>;
  refreshImages: (productId: string) => Promise<ProductImage[]>;
}

export function useImageSync(
  images: ProductImage[],
  setImages: React.Dispatch<React.SetStateAction<ProductImage[]>>
): UseImageSyncReturn {
  const persistImageMutation = useCallback(
    async (image: ProductImage): Promise<void> => {
      try {
        const sanitized: ProductImage = {
          ...image,
          order: image.order ?? 0,
          fileHash: image.fileHash || `hash-${Date.now()}-${image.id}`,
        };
        await db.productImages.put(sanitized);
        setImages((prev) => {
          const exists = prev.some((img) => img.id === sanitized.id);
          if (exists) {
            return prev.map((img) => (img.id === sanitized.id ? sanitized : img));
          }
          return [...prev, sanitized];
        });
      } catch (err) {
        console.error('Failed to persist image mutation in Dexie:', err);
        throw err;
      }
    },
    [setImages]
  );

  const deleteImage = useCallback(
    async (imageId: string): Promise<void> => {
      try {
        await db.productImages.delete(imageId);
        setImages((prev) => prev.filter((img) => img.id !== imageId));
      } catch (err) {
        console.error('Failed to delete image from Dexie:', err);
        throw err;
      }
    },
    [setImages]
  );

  const refreshImages = useCallback(
    async (productId: string): Promise<ProductImage[]> => {
      try {
        const list = await db.productImages.where('productId').equals(productId).toArray();
        return list;
      } catch (err) {
        console.error('Failed to refresh images from Dexie:', err);
        return images.filter((img) => img.productId === productId);
      }
    },
    [images]
  );

  return {
    persistImageMutation,
    deleteImage,
    refreshImages,
  };
}
