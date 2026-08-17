import React from 'react';
import { Product } from '../../types/store';
import { ProductVariant } from '../../types/productVariant';
import { UserAccount } from '../../types/store';
import { useMediaContext } from '../../context/MediaContext';
import { ImageDropZone } from './ImageDropZone';
import { ImageGalleryGrid } from './ImageGalleryGrid';
import { VariantImageLinker } from './VariantImageLinker';
import { X, Images, AlertCircle } from 'lucide-react';

interface ProductMediaManagerModalProps {
  product: Product;
  variants: ProductVariant[];
  currentUser?: UserAccount;
  onClose?: () => void;
  inline?: boolean;
}

export const ProductMediaManagerModal: React.FC<ProductMediaManagerModalProps> = ({
  product,
  variants,
  onClose,
  inline = false,
}) => {
  const {
    images,
    isUploading,
    error,
    selectedVariantId,
    setSelectedVariantId,
    uploadImages,
    deleteImage,
    assignImageToVariant,
    reorderImages,
    setPrimaryImage,
    clearError,
  } = useMediaContext();

  const handleFiles = async (files: File[]) => {
    try {
      await uploadImages({
        files,
        variantId: selectedVariantId || undefined,
        productId: product.id,
      });
    } catch {
      // Error state is captured and displayed via media context
    }
  };

  const handleMoveOrder = (id: string, direction: 'left' | 'right') => {
    if (!reorderImages) return;
    const index = images.findIndex((img) => img.id === id);
    if (index === -1) return;
    const targetIndex = direction === 'left' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= images.length) return;

    const newOrder = [...images];
    const [moved] = newOrder.splice(index, 1);
    newOrder.splice(targetIndex, 0, moved);
    reorderImages(newOrder.map((img) => img.id));
  };

  const content = (
    <div className="space-y-6">
      {error && (
        <div className="flex items-center justify-between rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-400">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-4 w-4" />
            <span>{error}</span>
          </div>
          {clearError && (
            <button
              onClick={clearError}
              className="text-xs font-medium underline hover:text-red-800 dark:hover:text-red-300"
            >
              Dismiss
            </button>
          )}
        </div>
      )}

      {variants.length > 0 && (
        <VariantImageLinker
          variants={variants}
          selectedVariantId={selectedVariantId}
          onSelectVariant={setSelectedVariantId}
        />
      )}

      <ImageDropZone onFilesSelected={handleFiles} isUploading={isUploading} />

      <ImageGalleryGrid
        images={images}
        variants={variants}
        selectedVariantId={selectedVariantId}
        onDelete={deleteImage}
        onSetPrimary={(id) => setPrimaryImage?.(id)}
        onAssignVariant={assignImageToVariant}
        onMove={handleMoveOrder}
      />
    </div>
  );

  if (inline) {
    return content;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget && onClose) onClose();
      }}
    >
      <div className="relative flex max-h-[90vh] w-full max-w-4xl flex-col rounded-lg bg-white shadow-xl dark:bg-gray-800">
        <div className="flex items-center justify-between border-b border-gray-200 p-4 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <Images className="h-5 w-5 text-gray-500 dark:text-gray-400" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Media Manager - {product.name}
            </h2>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-500 dark:hover:bg-gray-700"
              aria-label="Close"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4">{content}</div>

        {onClose && (
          <div className="flex justify-end border-t border-gray-200 p-4 dark:border-gray-700">
            <button
              onClick={onClose}
              className="rounded-lg bg-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
            >
              Close
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
