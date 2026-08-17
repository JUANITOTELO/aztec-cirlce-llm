import React, { useRef } from 'react';
import { ProductImage } from '../../types/productMedia';
import { ProductVariant } from '../../types/productVariant';
import { useProductImageCrud } from '../../hooks/useProductImageCrud';

interface Props {
  isOpen: boolean;
  productId: string;
  images: ProductImage[];
  variants: ProductVariant[];
  roleId?: string;
  onImagesUpdated: (updatedImages: ProductImage[]) => void;
  onClose: () => void;
}

export const ProductMediaManagerModal: React.FC<Props> = ({ isOpen, productId, images, variants, roleId, onImagesUpdated, onClose }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { isUploading, uploadProgress, error, uploadImageFile, deleteImage, setAsPrimary } = useProductImageCrud(productId, roleId);

  if (!isOpen) return null;

  const productImages = images.filter((img) => img.productId === productId);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    for (const file of files) {
      const newImage = await uploadImageFile(file);
      if (newImage) {
        const nextList = [...images, newImage];
        onImagesUpdated(nextList);
      }
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDelete = async (imageId: string) => {
    if (await deleteImage(imageId)) {
      onImagesUpdated(images.filter((img) => img.id !== imageId));
    }
  };

  const handlePrimary = async (imageId: string) => {
    const reordered = await setAsPrimary(imageId, images);
    onImagesUpdated(reordered);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div className="w-full max-w-2xl bg-slate-900 border border-slate-700 rounded-xl shadow-2xl flex flex-col max-h-[90vh]">
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-800/40">
          <h3 className="text-base font-bold text-slate-100">Galería Multimedia de Producto</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white">&times;</button>
        </div>
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          {error && <div className="p-3 bg-red-900/40 border border-red-700 text-red-200 text-xs rounded-lg">{error}</div>}
          <div className="flex items-center justify-between">
            <input type="file" ref={fileInputRef} onChange={handleFileChange} multiple accept="image/png, image/jpeg, image/webp" className="hidden" />
            <button type="button" onClick={() => fileInputRef.current?.click()} disabled={isUploading} className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-lg shadow disabled:opacity-50">
              {isUploading ? 'Subiendo...' : '+ Subir Imágenes'}
            </button>
          </div>
          <div className="grid grid-cols-3 gap-4 pt-2">
            {productImages.map((img) => {
              const linkedVariant = variants.find((v) => v.id === img.variantId);
              return (
                <div key={img.id} className="relative group bg-slate-950 border border-slate-800 rounded-lg p-2 flex flex-col items-center">
                  <img src={img.url} alt={img.fileName} className="w-full h-32 object-cover rounded mb-2 border border-slate-700/50" />
                  {img.isPrimary && <span className="absolute top-3 left-3 px-2 py-0.5 bg-emerald-600 text-[10px] font-bold text-white rounded shadow">Principal</span>}
                  <span className="text-[11px] text-slate-400 truncate w-full text-center">{img.fileName}</span>
                  {linkedVariant && <span className="text-[10px] text-cyan-400">Var: {linkedVariant.name}</span>}
                  <div className="flex gap-1.5 mt-2 w-full justify-center">
                    {!img.isPrimary && (
                      <button onClick={() => handlePrimary(img.id)} className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-[10px] text-cyan-300 rounded border border-cyan-800">
                        Establecer Principal
                      </button>
                    )}
                    <button onClick={() => handleDelete(img.id)} className="px-2 py-1 bg-red-900/60 hover:bg-red-800 text-[10px] text-red-200 rounded border border-red-700">
                      Eliminar
                    </button>
                  </div>
                </div>
              );
            })}
            {productImages.length === 0 && <p className="col-span-3 text-center py-8 text-slate-400 text-sm italic">No hay imágenes cargadas para este producto.</p>}
          </div>
        </div>
      </div>
    </div>
  );
};
