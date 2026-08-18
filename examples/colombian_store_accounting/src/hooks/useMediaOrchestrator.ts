import { useState, useEffect, useCallback } from 'react';
import { ProductImage, ImageUploadPayload } from '../types/productMedia';
import { ProductVariant } from '../types/productVariant';
import { UserAccount } from '../types/store';
import { db, addTransactionToQueue } from '../db/dexie';
import { validateImageBuffer, compressAndOptimizeImage } from '../engine/imageOptimizer';
import { logVariantMutation } from '../engine/variantAuditLogger';
import { hasPermission } from '../types/permissions';
import { INITIAL_PRODUCT_IMAGES } from '../constants/mockVariants';
import { BackendSyncEngine } from '../engine/backendSyncEngine';

export const GLOBAL_VARIANT_ID = 'product_global';
const MAX_IMAGE_SIZE_MB = 50;
const SUPPORTED_FORMATS = ['image/jpeg', 'image/png', 'image/webp'];

export interface UseMediaOrchestratorProps {
  productId?: string;
  variants?: ProductVariant[];
  currentUser?: UserAccount;
  initialImages?: ProductImage[];
  onImagesUpdated?: (images: ProductImage[]) => void;
}

async function computeFileSha256(file: File): Promise<string> {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  } catch (err) {
    return `hash-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
  }
}

const defaultUser: UserAccount = {
  id: 'usr-admin',
  name: 'Administrador',
  email: 'admin@pos.local',
  roleId: 'role-admin',
  role: 'admin',
  permissions: ['*'],
  isActive: true,
};

export function useMediaOrchestrator({
  productId = '',
  variants = [],
  currentUser = defaultUser,
  initialImages = [],
  onImagesUpdated,
}: UseMediaOrchestratorProps) {
  const effectiveUser = currentUser || defaultUser;
  const [images, setImages] = useState<ProductImage[]>(initialImages);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedVariantId, setSelectedVariantId] = useState<string | null>(null);

  const canManageMedia = hasPermission(effectiveUser, 'products.manage_media');

  const refreshImages = useCallback(async () => {
    setIsLoading(true);
    try {
      let records: ProductImage[] = [];
      if (productId) {
        records = await db.productImages
          .where('productId')
          .equals(productId)
          .sortBy('order');
        if (records.length === 0 && initialImages.length > 0) {
          records = initialImages;
        }
      } else {
        records = await db.productImages.toCollection().sortBy('order');
        if (records.length === 0) {
          records = INITIAL_PRODUCT_IMAGES;
        }
      }

      setImages(records);
      if (onImagesUpdated) onImagesUpdated(records);
    } catch (err: any) {
      const errorMsg = err?.message || 'Error al cargar imágenes de IndexedDB';
      setError(errorMsg);
      const fallback = productId
        ? INITIAL_PRODUCT_IMAGES.filter((img) => img.productId === productId)
        : INITIAL_PRODUCT_IMAGES;
      setImages(fallback.length > 0 ? fallback : initialImages);
    } finally {
      setIsLoading(false);
    }
  }, [productId, onImagesUpdated, initialImages]);

  useEffect(() => {
    refreshImages();
  }, [refreshImages]);

  const uploadImages = useCallback(async (payload: ImageUploadPayload): Promise<ProductImage[]> => {
    if (!canManageMedia) {
      const msg = 'No tiene permisos para subir imágenes';
      setError(msg);
      throw new Error(msg);
    }
    const filesToUpload = payload.files || (payload.file ? [payload.file] : []);
    if (filesToUpload.length === 0) return [];

    setIsUploading(true);
    setError(null);

    const createdImages: ProductImage[] = [];
    try {
      for (const file of filesToUpload) {
        if (file.size > MAX_IMAGE_SIZE_MB * 1024 * 1024) {
          throw new Error(`Archivo ${file.name} excede ${MAX_IMAGE_SIZE_MB}MB`);
        }
        if (!SUPPORTED_FORMATS.includes(file.type)) {
          throw new Error(`Formato ${file.type} no soportado. Use JPEG, PNG o WEBP`);
        }
      }

      const currentMaxOrder = images.length > 0 ? Math.max(...images.map((i) => i.order || 0)) : 0;

      for (let i = 0; i < filesToUpload.length; i++) {
        const file = filesToUpload[i];
        try {
          await validateImageBuffer(file);
          const optimized = await compressAndOptimizeImage(file);
          const fileHash = await computeFileSha256(file);

          const existingWithHash = await db.productImages
            .where('productId')
            .equals(productId)
            .filter((img) => img.fileHash === fileHash)
            .first();

          if (existingWithHash) {
            continue;
          }

          const newImg: ProductImage = {
            id: `img-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
            productId: productId || payload.productId || '',
            variantId: payload.variantId,
            url: optimized.base64,
            order: currentMaxOrder + i + 1,
            isPrimary: images.length === 0 && createdImages.length === 0 && i === 0,
            fileName: file.name,
            fileSize: optimized.sizeBytes,
            mimeType: 'image/webp',
            fileHash,
            createdAt: new Date().toISOString(),
          };
          createdImages.push(newImg);
        } catch (fileErr: any) {
          throw new Error(`Error procesando ${file.name}: ${fileErr.message}`);
        }
      }

      if (createdImages.length > 0) {
        await db.productImages.bulkAdd(createdImages);
        for (const img of createdImages) {
          BackendSyncEngine.saveImage(productId, img);
        }
        await addTransactionToQueue('VARIANT_MUTATION', {
          action: 'IMAGE_UPLOAD',
          productId,
          variantId: payload.variantId,
          images: createdImages,
        });
        await refreshImages();
      }

      return createdImages;
    } catch (err: any) {
      setError(err?.message || 'Fallo durante la carga y optimización');
      throw err;
    } finally {
      setIsUploading(false);
    }
  }, [canManageMedia, images, productId, refreshImages]);

  const deleteImage = useCallback(async (imageId: string) => {
    if (!canManageMedia) {
      const msg = 'Sin permiso para eliminar multimedia';
      setError(msg);
      throw new Error(msg);
    }
    try {
      const target = await db.productImages.get(imageId);
      if (!target) return;
      await db.productImages.delete(imageId);
      await logVariantMutation(
        target.variantId || GLOBAL_VARIANT_ID,
        productId,
        'IMAGE_DELETE',
        effectiveUser.id
      );
      await refreshImages();
    } catch (err: any) {
      setError(err?.message || 'Error al eliminar imagen');
    }
  }, [canManageMedia, productId, effectiveUser.id, refreshImages]);

  const assignImageToVariant = useCallback(async (imageId: string, variantId: string | null) => {
    if (!canManageMedia) {
      const msg = 'Sin permiso para actualizar multimedia';
      setError(msg);
      throw new Error(msg);
    }
    try {
      const target = await db.productImages.get(imageId);
      if (!target) return;
      await db.productImages.update(imageId, { variantId: variantId || undefined });
      await logVariantMutation(
        variantId || GLOBAL_VARIANT_ID,
        productId,
        'IMAGE_ASSIGN_VARIANT',
        effectiveUser.id
      );
      await refreshImages();
    } catch (err: any) {
      setError(err?.message || 'Error al asignar imagen a variante');
    }
  }, [canManageMedia, productId, effectiveUser.id, refreshImages]);

  const setPrimaryImage = useCallback(async (imageId: string) => {
    if (!canManageMedia) {
      const msg = 'Sin permiso para actualizar multimedia';
      setError(msg);
      throw new Error(msg);
    }
    try {
      const allImages = await db.productImages.where('productId').equals(productId).toArray();
      for (const img of allImages) {
        await db.productImages.update(img.id, { isPrimary: img.id === imageId });
      }
      await refreshImages();
    } catch (err: any) {
      setError(err?.message || 'Error al marcar imagen principal');
    }
  }, [canManageMedia, productId, refreshImages]);

  const clearError = useCallback(() => setError(null), []);

  const reorderImages = useCallback(async (orderedIds: string[]) => {
    try {
      if (!orderedIds || orderedIds.length === 0) return;
      for (let i = 0; i < orderedIds.length; i++) {
        await db.productImages.update(orderedIds[i], { order: i });
      }
      await refreshImages();
    } catch (err: any) {
      setError(err?.message || 'Error al reordenar imágenes');
    }
  }, [refreshImages]);

  return {
    images,
    isLoading,
    isUploading,
    error,
    clearError,
    selectedVariantId,
    setSelectedVariantId,
    refreshImages,
    uploadImages,
    deleteImage,
    assignImageToVariant,
    reorderImages,
    setPrimaryImage,
  };
}
