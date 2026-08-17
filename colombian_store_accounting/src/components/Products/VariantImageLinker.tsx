import React from 'react';
import { ProductVariant } from '../../types/productVariant';
import { Link2, Layers } from 'lucide-react';

interface VariantImageLinkerProps {
  variants: ProductVariant[];
  currentVariantId?: string | null;
  selectedVariantId?: string | null;
  onSelectVariant: (variantId: string | null) => void;
  disabled?: boolean;
}

export const VariantImageLinker: React.FC<VariantImageLinkerProps> = ({
  variants,
  currentVariantId,
  selectedVariantId,
  onSelectVariant,
  disabled = false,
}) => {
  const activeId = selectedVariantId !== undefined ? selectedVariantId : currentVariantId;
  return (
    <div className="flex items-center gap-2 bg-slate-800/80 px-3 py-2 rounded-lg border border-slate-700/70">
      <Link2 className="w-4 h-4 text-emerald-400 shrink-0" />
      <label className="text-xs font-semibold text-slate-300 shrink-0 flex items-center gap-1">
        <Layers className="w-3.5 h-3.5 text-slate-400" />
        Vincular a:
      </label>
      <select
        value={currentVariantId || ''}
        disabled={disabled}
        onChange={(e) => onSelectVariant(e.target.value ? e.target.value : null)}
        className="bg-slate-900 border border-slate-700 text-xs rounded-md text-slate-200 px-2.5 py-1 focus:outline-none focus:border-emerald-500 flex-1"
      >
        <option value="">🖼️ Galería General (Producto)</option>
        {variants.map((v) => (
          <option key={v.id} value={v.id}>
            🏷️ {v.sku} - {v.name}
          </option>
        ))}
      </select>
    </div>
  );
};