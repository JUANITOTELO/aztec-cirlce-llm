import React, { useState, useEffect } from 'react';
import { ProductVariant, ProductVariantFormData } from '../../types/productVariant';
import { VariantAttributeForm } from './VariantAttributeForm';
import { validateVariantPayload, buildNewVariant } from '../../engine/variantCrudEngine';

interface Props {
  isOpen: boolean;
  productId: string;
  variantToEdit?: ProductVariant | null;
  allVariants: ProductVariant[];
  onSave: (variant: ProductVariant) => void;
  onClose: () => void;
  disabled?: boolean;
}

export const VariantEditModal: React.FC<Props> = ({ isOpen, productId, variantToEdit, allVariants, onSave, onClose, disabled }) => {
  const [formData, setFormData] = useState<ProductVariantFormData>({
    name: '', sku: '', barcode: '', price: 0, cost: 0, stock: 0, minStock: 0, isActive: true, attributes: {}
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (variantToEdit) {
      setFormData({
        name: variantToEdit.name, sku: variantToEdit.sku, barcode: variantToEdit.barcode || '',
        price: variantToEdit.price, cost: variantToEdit.cost, stock: variantToEdit.stock, minStock: variantToEdit.minStock,
        isActive: variantToEdit.isActive, attributes: { ...variantToEdit.attributes }
      });
    } else {
      setFormData({ name: '', sku: '', barcode: '', price: 0, cost: 0, stock: 0, minStock: 0, isActive: true, attributes: {} });
    }
    setErrors({});
  }, [variantToEdit, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validation = validateVariantPayload(formData, allVariants, variantToEdit?.id);
    if (!validation.isValid) {
      setErrors(validation.errors);
      return;
    }
    if (variantToEdit) {
      onSave({ ...variantToEdit, ...formData, updatedAt: new Date().toISOString() });
    } else {
      onSave(buildNewVariant(productId, formData));
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        <div className="px-6 py-4 border-b border-slate-800 flex justify-between items-center bg-slate-800/40">
          <h3 className="text-base font-bold text-slate-100">{variantToEdit ? 'Editar Variante' : 'Crear Nueva Variante'}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4 overflow-y-auto flex-1">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-slate-300 font-medium">Nombre *</label>
              <input type="text" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100" />
              {errors.name && <p className="text-xs text-red-400 mt-1">{errors.name}</p>}
            </div>
            <div>
              <label className="text-xs text-slate-300 font-medium">SKU *</label>
              <input type="text" value={formData.sku} onChange={e => setFormData({ ...formData, sku: e.target.value })} className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100" />
              {errors.sku && <p className="text-xs text-red-400 mt-1">{errors.sku}</p>}
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-slate-300 font-medium">Precio (COP)</label>
              <input type="number" value={formData.price} onChange={e => setFormData({ ...formData, price: Number(e.target.value) })} className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100" />
            </div>
            <div>
              <label className="text-xs text-slate-300 font-medium">Costo (COP)</label>
              <input type="number" value={formData.cost} onChange={e => setFormData({ ...formData, cost: Number(e.target.value) })} className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100" />
            </div>
            <div>
              <label className="text-xs text-slate-300 font-medium">Stock Inicial</label>
              <input type="number" value={formData.stock} onChange={e => setFormData({ ...formData, stock: Number(e.target.value) })} className="w-full mt-1 px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-sm text-slate-100" />
            </div>
          </div>
          <VariantAttributeForm attributes={formData.attributes || {}} onChange={attrs => setFormData({ ...formData, attributes: attrs })} disabled={disabled} />
          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm">Cancelar</button>
            <button type="submit" disabled={disabled} className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg text-sm">Guardar Variante</button>
          </div>
        </form>
      </div>
    </div>
  );
};
