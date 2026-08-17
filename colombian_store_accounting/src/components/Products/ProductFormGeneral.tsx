import React from 'react';
import { Product } from '../../types/store';
import { Category } from '../../types/category';
import { sanitizeVariantSku, sanitizeVariantName } from '../../engine/variantSanitization';

interface ProductFormGeneralProps {
  formData: Partial<Product>;
  onChange: (field: keyof Product, value: any) => void;
  categories: Category[];
  errors?: Record<string, string>;
}

export const ProductFormGeneral: React.FC<ProductFormGeneralProps> = ({
  formData,
  onChange,
  categories,
  errors = {},
}) => {
  const handleTextChange = (field: keyof Product, rawValue: string) => {
    if (field === 'sku') {
      onChange('sku', sanitizeVariantSku(rawValue));
    } else if (field === 'name') {
      onChange('name', sanitizeVariantName(rawValue));
    } else {
      onChange(field, rawValue);
    }
  };

  return (
    <div className="space-y-4 p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Nombre del Producto *</label>
          <input
            type="text"
            required
            value={formData.name || ''}
            onChange={(e) => handleTextChange('name', e.target.value)}
            placeholder="Ej. Café Juan Valdez Premium"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
          />
          {errors.name && <p className="text-rose-400 text-xs mt-1">{errors.name}</p>}
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">SKU Principal *</label>
          <input
            type="text"
            required
            value={formData.sku || ''}
            onChange={(e) => handleTextChange('sku', e.target.value)}
            placeholder="Ej. CF-001"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 font-mono"
          />
          {errors.sku && <p className="text-rose-400 text-xs mt-1">{errors.sku}</p>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Categoría *</label>
          <select
            value={formData.category || ''}
            onChange={(e) => onChange('category', e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
          >
            <option value="">Seleccione categoría...</option>
            {categories.map((c) => (
              <option key={c.id} value={c.name}>
                {c.name} ({c.ledgerAccountCode})
              </option>
            ))}
          </select>
          {errors.category && <p className="text-rose-400 text-xs mt-1">{errors.category}</p>}
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Código de Barras (EAN)</label>
          <input
            type="text"
            value={formData.barcode || ''}
            onChange={(e) => onChange('barcode', e.target.value)}
            placeholder="Ej. 77020101"
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 font-mono"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Precio Venta (COP) *</label>
          <input
            type="number"
            min="0"
            step="100"
            value={formData.price ?? 0}
            onChange={(e) => onChange('price', parseFloat(e.target.value) || 0)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Costo Unitario (COP)</label>
          <input
            type="number"
            min="0"
            step="100"
            value={formData.cost ?? 0}
            onChange={(e) => onChange('cost', parseFloat(e.target.value) || 0)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Stock Inicial</label>
          <input
            type="number"
            min="0"
            value={formData.stock ?? 0}
            onChange={(e) => onChange('stock', parseInt(e.target.value, 10) || 0)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500 font-mono"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-slate-300 mb-1">Tasa IVA DIAN</label>
          <select
            value={formData.ivaRate ?? 0.19}
            onChange={(e) => onChange('ivaRate', parseFloat(e.target.value))}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-emerald-500"
          >
            <option value={0.19}>19% (General)</option>
            <option value={0.05}>5% (Reducido)</option>
            <option value={0.00}>0% (Exento / Excluido)</option>
          </select>
        </div>
      </div>
    </div>
  );
};
