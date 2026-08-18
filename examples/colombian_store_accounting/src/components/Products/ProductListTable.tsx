import React from 'react';
import { Edit2, Trash2, Sliders, History, Package } from 'lucide-react';
import { Product } from '../../types/store';
import { ProductPermissions } from '../../types/product';
import { ProductImage } from '../../types/productMedia';
import { Category } from '../../types/category';
import { CategoryBadge } from '../../atoms/CategoryBadge';
import { formatCOP, formatPercent } from '../../utils/formatters';

interface ProductListTableProps {
  products: Product[];
  images?: ProductImage[];
  permissions?: Partial<ProductPermissions>;
  categories?: Category[];
  searchQuery?: string;
  onEdit: (product: Product) => void;
  onDelete: (id: string) => void;
  onAdjustStock?: (product: Product) => void;
  onViewHistory?: (product: Product) => void;
}

export function ProductListTable({
  products,
  images = [],
  permissions = { canViewCost: true, canEditProduct: true, canAdjustStock: true, canDeleteProduct: true, canViewPricingHistory: true },
  categories = [],
  searchQuery = '',
  onEdit,
  onDelete,
  onAdjustStock,
  onViewHistory,
}: ProductListTableProps) {
  const getCategoryColor = (catName: string) => {
    const found = categories.find((c) => c.name.toLowerCase() === (catName || '').toLowerCase());
    return found?.color || '#3B82F6';
  };

  const filteredProducts = products.filter((p) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (p.name || '').toLowerCase().includes(q) ||
      (p.sku || '').toLowerCase().includes(q) ||
      (p.category || '').toLowerCase().includes(q)
    );
  });

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-700 bg-slate-800/90 shadow-lg">
      <table className="w-full text-left text-sm text-slate-300">
        <thead className="bg-slate-900/90 text-xs uppercase font-semibold text-slate-400 border-b border-slate-700">
          <tr>
            <th className="px-4 py-3.5">Producto</th>
            <th className="px-4 py-3.5">Categoría</th>
            <th className="px-4 py-3.5">Precio Venta</th>
            <th className="px-4 py-3.5">Costo</th>
            <th className="px-4 py-3.5">Stock</th>
            <th className="px-4 py-3.5">IVA</th>
            <th className="px-4 py-3.5 text-right">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/60 font-sans">
          {filteredProducts.length === 0 ? (
            <tr>
              <td colSpan={7} className="px-4 py-8 text-center text-slate-400 text-sm">
                No se encontraron productos registrados con el criterio de búsqueda.
              </td>
            </tr>
          ) : (
            filteredProducts.map((p) => {
              const isLowStock = p.stock <= p.minStock;
              const imgUrl =
                images.find((img) => img.productId === p.id && (img.isPrimary || img.imageType === 'PRIMARY'))?.url ||
                images.find((img) => img.productId === p.id)?.url ||
                p.image;
              return (
                <tr key={p.id} className="hover:bg-slate-700/40 transition-colors">
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-slate-900 border border-slate-700/80 overflow-hidden shrink-0 flex items-center justify-center">
                        {imgUrl ? (
                          <img
                            src={imgUrl}
                            alt={p.name}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        ) : (
                          <Package className="w-4 h-4 text-slate-600" />
                        )}
                      </div>
                      <div>
                        <div className="font-semibold text-white">{p.name}</div>
                        <div className="text-xs text-slate-400 font-mono">SKU: {p.sku}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3.5">
                    <CategoryBadge name={p.category} color={getCategoryColor(p.category)} />
                  </td>
                  <td className="px-4 py-3.5 font-bold text-slate-100 font-mono">{formatCOP(p.price)}</td>
                  <td className="px-4 py-3.5 text-xs text-slate-400 font-mono">
                    {permissions?.canViewCost ? formatCOP(p.cost) : '••••••'}
                  </td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-semibold font-mono ${
                        isLowStock
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                      }`}
                    >
                      {p.stock} un.
                    </span>
                  </td>
                  <td className="px-4 py-3.5 text-xs text-slate-300 font-mono">{formatPercent(p.ivaRate)}</td>
                  <td className="px-4 py-3.5 text-right space-x-1 whitespace-nowrap">
                    {permissions?.canAdjustStock !== false && onAdjustStock && (
                      <button
                        onClick={() => onAdjustStock(p)}
                        className="p-1.5 text-slate-400 hover:text-sky-400 hover:bg-slate-700 rounded-lg transition-colors inline-block"
                        title="Ajustar Stock"
                      >
                        <Sliders className="w-4 h-4" />
                      </button>
                    )}
                    {permissions?.canViewPricingHistory !== false && onViewHistory && (
                      <button
                        onClick={() => onViewHistory(p)}
                        className="p-1.5 text-slate-400 hover:text-purple-400 hover:bg-slate-700 rounded-lg transition-colors inline-block"
                        title="Historial de Precios"
                      >
                        <History className="w-4 h-4" />
                      </button>
                    )}
                    {permissions?.canEditProduct !== false && (
                      <button
                        onClick={() => onEdit(p)}
                        className="p-1.5 text-slate-400 hover:text-emerald-400 hover:bg-slate-700 rounded-lg transition-colors inline-block"
                        title="Editar Producto"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                    )}
                    {permissions?.canDeleteProduct !== false && (
                      <button
                        onClick={() => onDelete(p.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-700 rounded-lg transition-colors inline-block"
                        title="Eliminar Producto"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </td>
                </tr>
              );
            })
          )}
        </tbody>
      </table>
    </div>
  );
}
