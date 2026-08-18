import React, { useMemo } from 'react';
import { Package, AlertTriangle, DollarSign, Layers } from 'lucide-react';
import { Product } from '../../types/store';
import { Category } from '../../types/category';
import { formatCOP } from '../../utils/formatters';

interface ProductStatsCardsProps {
  products: Product[];
  categories?: Category[];
  canViewCost?: boolean;
}

export function ProductStatsCards({ products, categories = [], canViewCost = true }: ProductStatsCardsProps) {
  const stats = useMemo(() => {
    const totalProducts = products.length;
    const lowStock = products.filter((p) => p.stock <= p.minStock).length;
    const inventoryValue = products.reduce((acc, p) => acc + (canViewCost ? p.cost : p.price) * p.stock, 0);
    const activeCategoriesCount = categories.length || new Set(products.map((p) => p.category)).size;
    return { totalProducts, lowStock, inventoryValue, activeCategoriesCount };
  }, [products, categories, canViewCost]);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-400 font-medium">Total Productos</p>
          <h3 className="text-xl font-bold text-white mt-1 font-mono">{stats.totalProducts}</h3>
        </div>
        <div className="p-3 bg-sky-500/20 text-sky-400 rounded-lg border border-sky-500/30">
          <Package className="w-5 h-5" />
        </div>
      </div>

      <div className="bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-400 font-medium">Stock Bajo / Alerta</p>
          <h3 className="text-xl font-bold text-rose-400 mt-1 font-mono">{stats.lowStock}</h3>
        </div>
        <div className="p-3 bg-rose-500/20 text-rose-400 rounded-lg border border-rose-500/30">
          <AlertTriangle className="w-5 h-5" />
        </div>
      </div>

      <div className="bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-400 font-medium">Categorías Activas</p>
          <h3 className="text-xl font-bold text-purple-400 mt-1 font-mono">{stats.activeCategoriesCount}</h3>
        </div>
        <div className="p-3 bg-purple-500/20 text-purple-400 rounded-lg border border-purple-500/30">
          <Layers className="w-5 h-5" />
        </div>
      </div>

      <div className="bg-slate-800/90 border border-slate-700 p-4 rounded-xl shadow-lg flex items-center justify-between">
        <div>
          <p className="text-xs text-slate-400 font-medium">Valor Inventario</p>
          <h3 className="text-xl font-bold text-emerald-400 mt-1 font-mono">{formatCOP(stats.inventoryValue)}</h3>
        </div>
        <div className="p-3 bg-emerald-500/20 text-emerald-400 rounded-lg border border-emerald-500/30">
          <DollarSign className="w-5 h-5" />
        </div>
      </div>
    </div>
  );
}
