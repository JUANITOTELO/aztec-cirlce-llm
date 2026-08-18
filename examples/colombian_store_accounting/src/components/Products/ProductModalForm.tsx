import React, { useState, useEffect } from 'react';
import { X, Save, AlertCircle, Package } from 'lucide-react';
import { Product } from '../../types/store';
import { Category } from '../../types/category';
import { CategorySelector } from './CategorySelector';

interface ProductModalFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: any) => void;
  initialData?: Product | null;
  categories: Category[];
  onQuickAddCategory?: (name: string) => void;
}

export const ProductModalForm: React.FC<ProductModalFormProps> = ({
  isOpen,
  onClose,
  onSave,
  initialData,
  categories,
  onQuickAddCategory,
}) => {
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    category: '',
    price: 0,
    cost: 0,
    stock: 0,
    description: '',
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name || '',
        sku: initialData.sku || '',
        category: initialData.category || '',
        price: initialData.price || 0,
        cost: initialData.cost || 0,
        stock: initialData.stock ?? 0,
        description: (initialData as any).description || '',
      });
    } else {
      setFormData({
        name: '',
        sku: '',
        category: categories[0]?.name || '',
        price: 0,
        cost: 0,
        stock: 0,
        description: '',
      });
    }
  }, [initialData, categories, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setError('El nombre del producto es obligatorio');
      return;
    }
    if (formData.price < 0 || formData.stock < 0) {
      setError('Precio y stock no pueden ser negativos');
      return;
    }
    setError(null);
    onSave(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden border border-slate-700 animate-in fade-in duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/80 bg-slate-850">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Package className="w-5 h-5 text-emerald-400" />
            {initialData ? 'Editar Producto' : 'Nuevo Producto'}
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl flex items-center gap-2 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Nombre del Producto
              </label>
              <input
                type="text"
                required
                placeholder="ej: Café Juan Valdez 500g"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                SKU / Código
              </label>
              <input
                type="text"
                placeholder="ej: AB-001"
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                className="w-full px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm font-mono"
              />
            </div>

            <div>
              <CategorySelector
                categories={categories}
                selectedCategory={formData.category}
                onSelect={(category) => setFormData({ ...formData, category })}
                onQuickAdd={onQuickAddCategory}
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Precio de Venta ($ COP)
              </label>
              <input
                type="number"
                step="1"
                min="0"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })}
                className="w-full px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm font-mono font-semibold"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Stock Inicial (Unidades)
              </label>
              <input
                type="number"
                min="0"
                value={formData.stock}
                onChange={(e) => setFormData({ ...formData, stock: parseInt(e.target.value, 10) || 0 })}
                className="w-full px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm font-mono"
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-700/80">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 bg-slate-700/50 hover:bg-slate-700 text-slate-300 border border-slate-600 rounded-xl text-sm font-medium transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-emerald-900/40 transition-colors"
            >
              <Save className="w-4 h-4" />
              Guardar Producto
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
