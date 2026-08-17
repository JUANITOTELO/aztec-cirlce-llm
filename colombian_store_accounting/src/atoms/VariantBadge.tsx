import React from 'react';
import { ProductVariant } from '../types/productVariant';

interface VariantBadgeProps {
  variant: ProductVariant;
  showStock?: boolean;
  onClick?: () => void;
}

export const VariantBadge: React.FC<VariantBadgeProps> = ({
  variant,
  showStock = false,
  onClick,
}) => {
  const attrSummary = Object.values(variant.attributes || {})
    .filter(Boolean)
    .join(' · ');

  return (
    <span
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium border ${
        variant.isActive
          ? 'bg-sky-950/60 text-sky-300 border-sky-700/50'
          : 'bg-slate-800 text-slate-400 border-slate-700'
      } ${onClick ? 'cursor-pointer hover:bg-sky-900/60' : ''}`}
    >
      <span className="font-mono font-bold">{variant.sku}</span>
      {attrSummary && <span className="text-slate-300">({attrSummary})</span>}
      {showStock && (
        <span
          className={`ml-1 px-1 rounded text-[10px] ${
            variant.stock <= variant.minStock
              ? 'bg-rose-900/80 text-rose-200'
              : 'bg-emerald-900/80 text-emerald-200'
          }`}
        >
          {variant.stock} u
        </span>
      )}
      {variant.isDefault && (
        <span className="bg-amber-900/60 text-amber-300 text-[9px] px-1 rounded uppercase font-semibold">
          Def
        </span>
      )}
    </span>
  );
};