import { useState, useCallback } from 'react';
import { db, deleteVariantWithCascade } from '../db/dexie';
import { ProductVariant, ProductVariantFormData } from '../types/productVariant';
import { ProductImage } from '../types/productMedia';
import { buildNewVariant, buildNewImage } from '../engine/variantCrudEngine';
import { validateVariantPayload } from '../engine/variantImageValidation';

export interface UseVariantImageTransactionProps {
  productId: string;
  userId?: string;
  userRole?: string;
  onVariantsChanged?: (variants: ProductVariant[]) => void;
  onImagesChanged?: (images: ProductImage[]) => void;
}

export function useVariantImageTransaction({ productId, userId = 'system', userRole = 'admin', onVariantsChanged, onImagesChanged }: UseVariantImageTransactionProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const role = (userRole || 'admin').toLowerCase();
  const isAuthorized = role === 'admin' || role === 'contador';
  const fetchProductVariants = useCallback(async () => {
    const vars = await db.productVariants.where('productId').equals(productId).toArray();
    onVariantsChanged?.(vars);
    return vars;
  }, [productId, onVariantsChanged]);

  const fetchProductImages = useCallback(async () => {
    const imgs = await db.productImages.where('productId').equals(productId).sortBy('order');
    onImagesChanged?.(imgs);
    return imgs;
  }, [productId, onImagesChanged]);

  const saveVariant = async (form: ProductVariantFormData, variantId?: string): Promise<ProductVariant> => {
    if (!isAuthorized) throw new Error('No tiene permisos para modificar variantes.');
    setLoading(true);
    setError(null);
    try {
      const allVariants = await db.productVariants.toArray();
      const existingSkus = allVariants.filter(v => v.id !== variantId).map(v => v.sku.toUpperCase());
      const existingBarcodes = allVariants.filter(v => v.id !== variantId && v.barcode).map(v => v.barcode!); 
      const validation = validateVariantPayload(form, existingSkus, existingBarcodes, variantId);
      if (!validation.isValid) {
        throw new Error(Object.values(validation.errors)[0]);
      }
      const result = await db.transaction('rw', db.productVariants, db.variantAuditLogs, async () => {
        if (variantId) {
          const existing = await db.productVariants.get(variantId);
          if (!existing) throw new Error('Variante no encontrada');
          const updated: ProductVariant = { ...existing, ...form, updatedAt: new Date().toISOString() };
          await db.productVariants.put(updated);
          await db.variantAuditLogs.add({ id: crypto.randomUUID(), variantId, productId, action: 'UPDATE', timestamp: new Date().toISOString(), userId, details: JSON.stringify(form) });
          return updated;
        } else {
          const created = buildNewVariant(productId, form);
          await db.productVariants.add(created);
          await db.variantAuditLogs.add({ id: crypto.randomUUID(), variantId: created.id, productId, action: 'CREATE', timestamp: new Date().toISOString(), userId, details: JSON.stringify(form) });
          return created;
        }
      });
      await fetchProductVariants();
      return result;
    } catch (err: any) {
      setError(err.message || 'Error al guardar variante');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteVariant = async (variantId: string) => {
    if (!isAuthorized) throw new Error('No tiene permisos para eliminar variantes.');
    setLoading(true);
    setError(null);
    try {
      await deleteVariantWithCascade(variantId);
      await Promise.all([fetchProductVariants(), fetchProductImages()]);
    } catch (err: any) {
      setError(err.message || 'Error al eliminar variante');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const saveImage = async (url: string, variantId?: string, isPrimary: boolean = false) => {
    if (!isAuthorized) throw new Error('No tiene permisos para subir imágenes.');
    setLoading(true);
    try {
      const existing = await db.productImages.where('productId').equals(productId).toArray();
      const order = existing.length;
      const newImg = buildNewImage(productId, variantId || '', url, isPrimary, order);
      await db.productImages.add(newImg);
      await fetchProductImages();
      return newImg;
    } catch (err: any) {
      setError(err.message || 'Error al guardar imagen');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const reorderImages = async (imageIdsInOrder: string[]) => {
    setLoading(true);
    try {
      await db.transaction('rw', db.productImages, async () => {
        for (let i = 0; i < imageIdsInOrder.length; i++) {
          await db.productImages.update(imageIdsInOrder[i], { order: i });
        }
      });
      await fetchProductImages();
    } catch (err: any) {
      setError(err.message || 'Error al reordenar imágenes');
    } finally {
      setLoading(false);
    }
  };

  const deleteImage = async (imageId: string) => {
    if (!isAuthorized) throw new Error('No tiene permisos para eliminar imágenes.');
    setLoading(true);
    try {
      await db.productImages.delete(imageId);
      await fetchProductImages();
    } catch (err: any) {
      setError(err.message || 'Error al eliminar imagen');
    } finally {
      setLoading(false);
    }
  };

  return { loading, error, saveVariant, deleteVariant, saveImage, reorderImages, deleteImage, fetchProductVariants, fetchProductImages };
}
