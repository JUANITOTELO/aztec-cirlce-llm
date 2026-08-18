import React, { useState } from 'react';
import { ProductImage } from '../../types/productMedia';
import { validateMediaFile, sanitizeFileName } from '../../engine/mediaValidation';
import { compressAndOptimizeImage, MediaValidationError } from '../../engine/imageOptimizer';
import { db } from '../../db/dexie';

interface ImageGalleryUploaderProps {
  productId: string;
  variantId?: string | null;
  images: ProductImage[];
  onImagesChange: (images: ProductImage[]) => void;
  canUpload: boolean;
  canDelete: boolean;
}

export const ImageGalleryUploader: React.FC<ImageGalleryUploaderProps> = ({
  productId,
  variantId = null,
  images,
  onImagesChange,
  canUpload,
  canDelete,
}) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.length) return;
    const file = e.target.files[0];
    setError(null);
    const validationErrors = validateMediaFile(file);
    if (validationErrors.length > 0) {
      setError(validationErrors.map((err) => err.message).join(' '));
      return;
    }
    setUploading(true);
    try {
      const optimized = await compressAndOptimizeImage(file);
      const newImage: ProductImage = {
        id: `img-${Date.now()}-${Math.random().toString(36).substring(2, 5)}`,
        productId,
        variantId,
        imageType: images.length === 0 ? 'PRIMARY' : 'GALLERY',
        url: optimized.base64,
        altText: sanitizeFileName(file.name),
        order: images.length,
        fileSize: optimized.sizeBytes,
        mimeType: 'image/webp',
        createdAt: new Date().toISOString(),
      };
      const updated = [...images, newImage];
      onImagesChange(updated);
      await db.productImages.put(newImage);
    } catch (err: any) {
      const message = err instanceof MediaValidationError ? err.message : 'Error al procesar la imagen.';
      setError(message);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!canDelete) return;
    const updated = images.filter((img) => img.id !== id);
    onImagesChange(updated);
    await db.productImages.delete(id);
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Galería de Imágenes</h4>
        {canUpload && (
          <label className="cursor-pointer bg-sky-600 hover:bg-sky-500 text-white text-xs px-2.5 py-1 rounded transition font-medium">
            {uploading ? 'Cargando...' : '+ Subir Imagen'}
            <input type="file" accept="image/jpeg,image/png,image/webp" onChange={handleFile} disabled={uploading} className="hidden" />
          </label>
        )}
      </div>
      {error && <div className="p-2 text-xs bg-rose-900/50 text-rose-200 border border-rose-700 rounded">{error}</div>}
      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
        {images.map((img) => (
          <div key={img.id} className="relative group aspect-square rounded bg-slate-800 border border-slate-700 overflow-hidden">
            <img src={img.url} alt={img.altText} className="w-full h-full object-cover" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
            {img.imageType === 'PRIMARY' && (
              <span className="absolute top-1 left-1 bg-amber-500 text-slate-950 text-[9px] font-bold px-1 rounded shadow">Principal</span>
            )}
            {canDelete && (
              <button
                type="button"
                onClick={() => handleDelete(img.id)}
                className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 bg-rose-600 hover:bg-rose-500 text-white rounded p-0.5 text-xs transition"
              >
                ✕
              </button>
            )}
          </div>
        ))}
        {images.length === 0 && (
          <div className="col-span-full py-4 text-center text-xs text-slate-500 border border-dashed border-slate-700 rounded">
            Sin imágenes asociadas.
          </div>
        )}
      </div>
    </div>
  );
};
