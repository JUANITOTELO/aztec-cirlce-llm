import React, { useState, useEffect } from 'react';
import { ProductVariant } from '../../types/productVariant';
import { UserAccount } from '../../types/store';
import { useMediaContext } from '../../context/MediaContext';
import { ImageDropZone } from './ImageDropZone';
import { ImageGalleryGrid } from './ImageGalleryGrid';
import { X, Layers, Save, Trash2, Image as ImageIcon } from 'lucide-react';

interface VariantEditModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (variant: ProductVariant) => void;
  onDelete?: (variantId: string) => void;
  variant: ProductVariant | null;
  productId: string;
  currentUser: UserAccount;
}

export const VariantEditModal: React.FC<VariantEditModalProps> = ({
  isOpen,
  onClose,
  onSave,
  onDelete,
  variant,
  productId,
  currentUser,
}) => {
  const [sku, setSku] = useState('');
  const [name, setName] = useState('');
  const [price, setPrice] = useState(0);
  const [cost, setCost] = useState(0);
  const [stock, setStock] = useState(0);
  const [activeTab, setActiveTab] = useState<'info' | 'images'>('info');

  const { images, isUploading, uploadImages, deleteImage, assignImageToVariant, setPrimaryImage } = useMediaContext();

  useEffect(() => {
    if (variant) {
      setSku(variant.sku);
      setName(variant.name);
      setPrice(variant.price);
      setCost(variant.cost);
      setStock(variant.stock);
    }
  }, [variant]);

  if (!isOpen || !variant) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      ...variant,
      sku,
      name,
      price: Number(price),
      cost: Number(cost),
      stock: Number(stock),
      updatedAt: new Date().toISOString(),
    });
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700/80 rounded-2xl w-full max-w-2xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-emerald-600/20 text-emerald-400 flex items-center justify-center border border-emerald-500/30">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Editar Variante: {variant.sku}</h3>
              <p className="text-xs text-slate-400">ID: {variant.id}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex border-b border-slate-800 bg-slate-950/30 px-6 gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('info')}
            className={`py-2.5 px-3 text-xs font-semibold border-b-2 transition-colors ${
              activeTab === 'info' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400'
            }`}
          >
            Información y Precios
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('images')}
            className={`py-2.5 px-3 text-xs font-semibold border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'images' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-slate-400'
            }`}
          >
            <ImageIcon className="w-3.5 h-3.5" /> Imágenes de la Variante
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          {activeTab === 'info' ? (
            <form onSubmit={handleSave} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">SKU</label>
                  <input
                    value={sku}
                    onChange={(e) => setSku(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Nombre</label>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Precio COP</label>
                  <input
                    type="number"
                    value={price}
                    onChange={(e) => setPrice(Number(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Costo COP</label>
                  <input
                    type="number"
                    value={cost}
                    onChange={(e) => setCost(Number(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Stock</label>
                  <input
                    type="number"
                    value={stock}
                    onChange={(e) => setStock(Number(e.target.value))}
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100"
                  />
                </div>
              </div>
              <div className="flex justify-between items-center pt-4 border-t border-slate-800">
                {onDelete && (
                  <button
                    type="button"
                    onClick={() => { onDelete(variant.id); onClose(); }}
                    className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1.5"
                  >
                    <Trash2 className="w-4 h-4" /> Eliminar Variante
                  </button>
                )}
                <div className="flex gap-2 ml-auto">
                  <button type="button" onClick={onClose} className="px-4 py-2 text-xs text-slate-300 hover:bg-slate-800 rounded-lg">
                    Cancelar
                  </button>
                  <button type="submit" className="px-4 py-2 text-xs bg-emerald-600 hover:bg-emerald-500 font-semibold text-white rounded-lg flex items-center gap-1.5">
                    <Save className="w-4 h-4" /> Guardar Cambios
                  </button>
                </div>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <ImageDropZone
                onFilesSelected={(files) =>
                  uploadImages({
                    files,
                    productId,
                    variantId: variant.id,
                  })
                }
                isUploading={isUploading}
              />
              <ImageGalleryGrid
                images={images.filter((img) => img.variantId === variant.id)}
                onDelete={(imageId) => deleteImage(imageId)}
                onSetPrimary={(imageId) => setPrimaryImage?.(imageId)}
                onAssignVariant={(imageId, vId) => assignImageToVariant(imageId, vId)}
                onMove={() => {}}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
