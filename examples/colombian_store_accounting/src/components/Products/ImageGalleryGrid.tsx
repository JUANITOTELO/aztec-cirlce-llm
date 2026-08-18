import React from 'react';
import { ProductImage } from '../../types/productMedia';
import { ProductVariant } from '../../types/productVariant';
import { Trash2, Star, ArrowLeft, ArrowRight, Tag } from 'lucide-react';

interface ImageGalleryGridProps {
  images: ProductImage[];
  variants?: ProductVariant[];
  selectedVariantId?: string | null;
  onDelete: (id: string) => void;
  onSetPrimary: (id: string) => void;
  onAssignVariant: (id: string, variantId: string | null) => void;
  onMove: (id: string, direction: 'left' | 'right') => void;
}

export const ImageGalleryGrid: React.FC<ImageGalleryGridProps> = ({
  images,
  variants = [],
  selectedVariantId,
  onDelete,
  onSetPrimary,
  onAssignVariant,
  onMove,
}) => {
  const filteredImages = selectedVariantId
    ? images.filter((img) => (img.variantId ?? (img as any).variant_id) === selectedVariantId)
    : images;

  if (filteredImages.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No images available.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {filteredImages.map((image, index) => {
        const isPrimary = Boolean(image.isPrimary ?? (image as any).is_primary);
        const variantId = image.variantId ?? (image as any).variant_id ?? null;

        return (
          <div
            key={image.id}
            className={`relative group border rounded-lg overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow ${
              isPrimary ? 'ring-2 ring-blue-500' : 'border-gray-200'
            }`}
          >
            <div className="aspect-square w-full bg-gray-100 relative flex items-center justify-center">
              <img
                src={image.url}
                alt={(image as any).altText || (image as any).alt_text || 'Product image'}
                loading="lazy"
                className="w-full h-full object-cover"
                onError={(e) => { e.currentTarget.style.backgroundColor = '#f3f4f6'; e.currentTarget.style.display = 'none'; }}
              />
              {isPrimary && (
                <span className="absolute top-2 left-2 bg-blue-500 text-white text-xs font-semibold px-2 py-0.5 rounded shadow">
                  Primary
                </span>
              )}
              {!image.url && (
                <div className="absolute inset-0 flex items-center justify-center bg-gray-200 text-gray-500 text-xs">
                  No image
                </div>
              )}
            </div>

            <div className="p-2 space-y-2">
              <div className="flex items-center justify-between gap-1">
                <button
                  type="button"
                  onClick={() => onMove(image.id, 'left')}
                  disabled={index === 0}
                  className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Move left"
                >
                  <ArrowLeft className="w-4 h-4" />
                </button>

                <button
                  type="button"
                  onClick={() => onSetPrimary(image.id)}
                  className={`p-1 rounded hover:bg-gray-100 ${
                    isPrimary ? 'text-yellow-500' : 'text-gray-400 hover:text-yellow-500'
                  }`}
                  title={isPrimary ? 'Primary image' : 'Set as primary'}
                >
                  <Star className={`w-4 h-4 ${isPrimary ? 'fill-current' : ''}`} />
                </button>

                <button
                  type="button"
                  onClick={() => onDelete(image.id)}
                  className="p-1 text-gray-400 hover:text-red-600 rounded hover:bg-gray-100"
                  title="Delete image"
                >
                  <Trash2 className="w-4 h-4" />
                </button>

                <button
                  type="button"
                  onClick={() => onMove(image.id, 'right')}
                  disabled={index === filteredImages.length - 1}
                  className="p-1 text-gray-500 hover:text-gray-700 disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Move right"
                >
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>

              {variants && variants.length > 0 && (
                <div className="flex items-center gap-1 text-xs">
                  <Tag className="w-3 h-3 text-gray-400 flex-shrink-0" />
                  <select
                    value={variantId || ''}
                    onChange={(e) => onAssignVariant(image.id, e.target.value || null)}
                    className="w-full text-xs border border-gray-300 rounded px-1.5 py-0.5 bg-white text-gray-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="">All Variants</option>
                    {variants.map((v) => (
                      <option key={v.id} value={v.id}>
                        {(v as any).name || (v as any).title || (v as any).sku || v.id}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default ImageGalleryGrid;