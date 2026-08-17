import React, { useState } from 'react';
import { ProductVariant, ProductVariantFormData, ProductVariantPermissions } from '../../types/productVariant';
import { ProductImage } from '../../types/productMedia';
import { formatCOP } from '../../utils/formatters';
import { ImageGalleryUploader } from './ImageGalleryUploader';

interface ProductVariantManagerProps {
  productId: string;
  productName: string;
  variants: ProductVariant[];
  images: ProductImage[];
  permissions: ProductVariantPermissions;
  onAddVariant: (productId: string, form: ProductVariantFormData) => Promise<any>;
  onDeleteVariant: (id: string) => Promise<void>;
  onImagesChange: (images: ProductImage[]) => void;
  onClose: () => void;
}

export const ProductVariantManager: React.FC<ProductVariantManagerProps> = ({
  productId,
  productName,
  variants,
  images,
  permissions,
  onAddVariant,
  onDeleteVariant,
  onImagesChange,
  onClose,
}) => {
  const [form, setForm] = useState<ProductVariantFormData>({
    sku: '', name: '', barcode: '', price: 0, cost: 0, stock: 0, minStock: 0,
    attributes: { size: '', color: '', flavor: '' }, isDefault: false, isActive: true,
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.sku || !form.name) return;
    setSubmitting(true);
    await onAddVariant(productId, form);
    setForm({
      sku: '', name: '', barcode: '', price: 0, cost: 0, stock: 0, minStock: 0,
      attributes: { size: '', color: '', flavor: '' }, isDefault: false, isActive: true,
    });
    setSubmitting(false);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-lg max-w-2xl w-full p-5 space-y-4 max-h-[90vh] overflow-y-auto text-slate-200">
        <div className="flex justify-between items-center border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-lg font-bold text-sky-400">Variaciones & Imágenes</h3>
            <p className="text-xs text-slate-400 font-medium">{productName} (ID: {productId})</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-lg font-bold">✕</button>
        </div>
        <ImageGalleryUploader
          productId={productId}
          images={images}
          onImagesChange={onImagesChange}
          canUpload={permissions.canUploadImages}
          canDelete={permissions.canDeleteImages}
        />
        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Variaciones Registradas</h4>
          <div className="divide-y divide-slate-800 border border-slate-800 rounded bg-slate-950/50">
            {variants.filter((v) => v.productId === productId).map((v) => (
              <div key={v.id} className="p-2.5 flex items-center justify-between text-xs">
                <div>
                  <span className="font-bold text-sky-300 font-mono">{v.sku}</span> - {v.name}
                  <span className="text-slate-400 ml-2 font-mono">Stock: {v.stock} | {formatCOP(v.price)}</span>
                </div>
                {permissions.canDeleteVariant && (
                  <button onClick={() => onDeleteVariant(v.id)} className="text-rose-400 hover:text-rose-300 px-2 py-0.5 rounded border border-rose-800/40 bg-rose-950/40">
                    Eliminar
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
        {permissions.canCreateVariant && (
          <form onSubmit={handleSubmit} className="bg-slate-800/50 p-3 rounded border border-slate-700/60 space-y-2 text-xs">
            <span className="font-semibold text-sky-300 block">+ Agregar Nueva Variación</span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <input placeholder="SKU (ej: VAR-01)" value={form.sku} onChange={(e) => setForm({ ...form, sku: e.target.value })} className="bg-slate-900 border border-slate-700 rounded p-1.5" required />
              <input placeholder="Nombre Variación" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="bg-slate-900 border border-slate-700 rounded p-1.5" required />
              <input type="number" placeholder="Precio COP" value={form.price || ''} onChange={(e) => setForm({ ...form, price: Number(e.target.value) })} className="bg-slate-900 border border-slate-700 rounded p-1.5" required />
              <input type="number" placeholder="Stock Inicial" value={form.stock || ''} onChange={(e) => setForm({ ...form, stock: Number(e.target.value) })} className="bg-slate-900 border border-slate-700 rounded p-1.5" required />
            </div>
            <button type="submit" disabled={submitting} className="w-full bg-sky-600 hover:bg-sky-500 text-white font-medium py-1.5 rounded transition">
              {submitting ? 'Guardando...' : 'Registrar Variación'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};