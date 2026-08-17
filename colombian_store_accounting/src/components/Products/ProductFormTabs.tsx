import React from 'react';
import { Layers, Image, Info } from 'lucide-react';

export type ProductFormTab = 'general' | 'variants' | 'media';

interface ProductFormTabsProps {
  activeTab: ProductFormTab;
  setActiveTab: (tab: ProductFormTab) => void;
  variantCount: number;
  imageCount: number;
}

export const ProductFormTabs: React.FC<ProductFormTabsProps> = ({
  activeTab,
  setActiveTab,
  variantCount,
  imageCount,
}) => {
  return (
    <div className="flex border-b border-slate-800 bg-slate-950/60 px-6 pt-3 gap-2">
      <button
        type="button"
        onClick={() => setActiveTab('general')}
        className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors ${
          activeTab === 'general'
            ? 'bg-slate-900 text-emerald-400 border-t-2 border-l border-r border-emerald-500 border-b-transparent'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
        }`}
      >
        <Info className="w-4 h-4" />
        <span>Información General</span>
      </button>

      <button
        type="button"
        onClick={() => setActiveTab('variants')}
        className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors ${
          activeTab === 'variants'
            ? 'bg-slate-900 text-emerald-400 border-t-2 border-l border-r border-emerald-500 border-b-transparent'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
        }`}
      >
        <Layers className="w-4 h-4" />
        <span>Variantes y Atributos</span>
        {variantCount > 0 && (
          <span className="ml-1.5 px-1.5 py-0.5 text-[10px] rounded-full bg-emerald-500/20 text-emerald-300 font-mono">
            {variantCount}
          </span>
        )}
      </button>

      <button
        type="button"
        onClick={() => setActiveTab('media')}
        className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold rounded-t-lg transition-colors ${
          activeTab === 'media'
            ? 'bg-slate-900 text-emerald-400 border-t-2 border-l border-r border-emerald-500 border-b-transparent'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
        }`}
      >
        <Image className="w-4 h-4" />
        <span>Galería de Imágenes</span>
        {imageCount > 0 && (
          <span className="ml-1.5 px-1.5 py-0.5 text-[10px] rounded-full bg-sky-500/20 text-sky-300 font-mono">
            {imageCount}
          </span>
        )}
      </button>
    </div>
  );
};
