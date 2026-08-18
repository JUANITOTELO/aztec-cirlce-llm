import React, { useState } from 'react';
import { ProductVariant } from '../../types/productVariant';
import { ProductImage } from '../../types/productMedia';
import { VariantBadge } from '../../atoms/VariantBadge';
import { VariantEditModal } from './VariantEditModal';
import { ProductMediaManagerModal } from './ProductMediaManagerModal';
import { useVariantImageTransaction } from '../../hooks/useVariantImageTransaction';
import { formatCOP } from '../../utils/formatters';

interface ProductVariantManagerProps {
  productId: string;
  variants?: ProductVariant[];
  images?: ProductImage[];
  userId?: string;
  userRole?: string;
  productPrice?: number;
  productCost?: number;
  productSku?: string;
  onVariantsUpdated?: (variants: ProductVariant[]) => void;
  onImagesUpdated?: (images: ProductImage[]) => void;
  canViewCost?: boolean;
}

export const ProductVariantManager: React.FC<ProductVariantManagerProps> = ({
  productId, variants = [], images = [], userId = 'system', userRole = 'admin', productPrice = 0, productCost = 0, productSku = '', onVariantsUpdated, onImagesUpdated, canViewCost = true,
}) => {
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isMediaOpen, setIsMediaOpen] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(null);
  const [activeVariantForMedia, setActiveVariantForMedia] = useState<string | undefined>(undefined);

  const { saveVariant, deleteVariant, saveImage, deleteImage, reorderImages } = useVariantImageTransaction({
    productId, userId, userRole, onVariantsChanged: onVariantsUpdated, onImagesChanged: onImagesUpdated,
  });

  const handleOpenAdd = () => { setSelectedVariant(null); setIsEditOpen(true); };
  const handleOpenEdit = (v: ProductVariant) => { setSelectedVariant(v); setIsEditOpen(true); };
  const handleOpenMedia = (variantId?: string) => { setActiveVariantForMedia(variantId); setIsMediaOpen(true); };

  return (
    <div className="bg-slate-900/60 border border-slate-800 rounded-xl p-4 mt-4">
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          <h4 className="font-bold text-sm text-slate-200">Variantes y Stock ({variants.length})</h4>
          <button onClick={() => handleOpenMedia()} className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-2.5 py-1 rounded border border-slate-700">📷 Fotos Producto</button>
        </div>
        <button onClick={handleOpenAdd} className="px-3 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded shadow flex items-center gap-1">+ Nueva Variante</button>
      </div>
      {variants.length === 0 ? (
        <p className="text-xs text-slate-500 italic py-2">Sin variantes configuradas. Este producto usa precio y stock general.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left text-slate-300">
            <thead className="bg-slate-800/80 text-slate-400 uppercase">
              <tr>
                <th className="p-2">SKU</th>
                <th className="p-2">Nombre</th>
                <th className="p-2">Precio</th>
                {canViewCost && <th className="p-2">Costo</th>}
                <th className="p-2">Stock</th>
                <th className="p-2 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {variants.map((v) => (
                <tr key={v.id} className="hover:bg-slate-800/40">
                  <td className="p-2 font-mono font-bold text-emerald-400">{v.sku}</td>
                  <td className="p-2"><VariantBadge variant={v} /></td>
                  <td className="p-2 text-white">{v.price ? formatCOP(v.price) : 'Base'}</td>
                  {canViewCost && <td className="p-2 text-slate-400">{v.cost ? formatCOP(v.cost) : 'Base'}</td>}
                  <td className="p-2"><span className={`px-2 py-0.5 rounded font-bold ${v.stock <= 5 ? 'bg-amber-950 text-amber-400' : 'bg-slate-800 text-emerald-300'}`}>{v.stock}</span></td>
                  <td className="p-2 text-right space-x-1">
                    <button onClick={() => handleOpenMedia(v.id)} title="Gestionar Fotos" className="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded">📸</button>
                    <button onClick={() => handleOpenEdit(v)} title="Editar Variante" className="px-2 py-1 bg-indigo-900/60 hover:bg-indigo-700 text-indigo-200 rounded">✏️</button>
                    <button onClick={() => deleteVariant(v.id)} title="Eliminar Variante" className="px-2 py-1 bg-red-950/80 hover:bg-red-800 text-red-300 rounded">🗑️</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {isEditOpen && (
        <VariantEditModal isOpen={isEditOpen} onClose={() => setIsEditOpen(false)} onSave={(form) => saveVariant(form, (form as any).id).then(() => {})} variant={selectedVariant} productId={productId} currentUser={{ id: userId, name: userId, email: '', roleId: `role-${userRole}`, role: userRole as any, permissions: ['*'], isActive: true }} />
      )}
      {isMediaOpen && (
        <ProductMediaManagerModal product={{ id: productId, name: '', sku: productSku || '', category: '', price: productPrice || 0, cost: productCost || 0, stock: 0, minStock: 0, ivaRate: 0.19 }} variants={variants} currentUser={{ id: userId, name: userId, email: '', roleId: `role-${userRole}`, role: userRole as any, permissions: ['*'], isActive: true }} onClose={() => setIsMediaOpen(false)} />
      )}
    </div>
  );
};
