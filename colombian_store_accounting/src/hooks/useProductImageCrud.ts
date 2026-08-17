import { useState } from 'react';
import { ProductImage } from '../types/productMedia';
import { hasPermission } from '../types/permissions';
import { validateMediaFile, fileToBase64 } from '../engine/mediaValidation';
import { buildNewImage } from '../engine/variantCrudEngine';
import { db } from '../db/dexie';

export interface ProductImageCrudHook {
  isUploading: boolean;
  uploadProgress: Record<string, number>;
  error: string | null;
  uploadImageFile: (file: File, variantId?: string) => Promise<ProductImage | null>;
  deleteImage: (imageId: string) => Promise<boolean>;
  setAsPrimary: (imageId: string, allImages: ProductImage[]) => Promise<ProductImage[]>;
  clearError: () => void;
}

export function useProductImageCrud(productId: string, roleId?: string): ProductImageCrudHook {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [error, setError] = useState<string | null>(null);

  const clearError = () => setError(null);

  const uploadImageFile = async (file: File, variantId?: string): Promise<ProductImage | null> => {
    if (!hasPermission(roleId, 'products:edit:media')) {
      setError('No cuenta con permisos de edición multimedia');
      return null;
    }
    const valErrors = validateMediaFile(file);
    if (valErrors.length > 0) {
      setError(valErrors[0].message || 'Archivo inválido');
      return null;
    }

    setIsUploading(true);
    setUploadProgress((p) => ({ ...p, [file.name]: 30 }));

    try {
      const base64Url = await fileToBase64(file);
      setUploadProgress((p) => ({ ...p, [file.name]: 75 }));

      const newImage = buildNewImage(productId, base64Url, file.name, file.size, file.type, variantId);
      await db.productImages.add(newImage);
      setUploadProgress((p) => ({ ...p, [file.name]: 100 }));
      return newImage;
    } catch (err: any) {
      setError(err?.message || 'Error al procesar la imagen');
      return null;
    } finally {
      setIsUploading(false);
    }
  };

  const deleteImage = async (imageId: string): Promise<boolean> => {
    if (!hasPermission(roleId, 'products:edit:media')) {
      setError('No cuenta con permisos de edición multimedia');
      return false;
    }
    try {
      await db.productImages.delete(imageId);
      return true;
    } catch (err: any) {
      setError(err?.message || 'Error al eliminar la imagen');
      return false;
    }
  };

  const setAsPrimary = async (imageId: string, allImages: ProductImage[]): Promise<ProductImage[]> => {
    if (!hasPermission(roleId, 'products:edit:media')) {
      setError('No cuenta con permisos de edición multimedia');
      return allImages;
    }
    const updated = allImages.map((img) => ({
      ...img,
      isPrimary: img.id === imageId,
    }));
    await db.transaction('rw', db.productImages, async () => {
      for (const item of updated) {
        await db.productImages.put(item);
      }
    });
    return updated;
  };

  return { isUploading, uploadProgress, error, uploadImageFile, deleteImage, setAsPrimary, clearError };
}
