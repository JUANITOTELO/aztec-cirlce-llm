import React, { useState } from 'react';
import { Product } from '../../types/store';
import { ProductImage } from '../../types/productMedia';
import { formatCOP } from '../../utils/formatters';
import { Package, AlertTriangle, Search, Plus, Edit2, CheckCircle2 } from 'lucide-react';

interface InventoryManagerProps {
  products: Product[];
  images?: ProductImage[];
  onUpdateStock: (id: string, newStock: number) => void;
}

export const InventoryManager: React.FC<InventoryManagerProps> = ({ products, images = [], onUpdateStock }) => {
  const [search, setSearch] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [newStockVal, setNewStockVal] = useState<number>(0);

  const filtered = products.filter(
    (p) =>
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.sku.toLowerCase().includes(search.toLowerCase()) ||
      p.category.toLowerCase().includes(search.toLowerCase())
  );

  const lowStockCount = products.filter((p) => p.stock <= p.minStock).length;

  const handleSaveStock = (id: string) => {
    onUpdateStock(id, newStockVal);
    setEditingId(null);
  };

  return (
    <div className="space-y-6">
      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-xl">
          <div className="text-xs text-slate-400 font-medium">Total Productos</div>
          <div className="text-2xl font-bold text-white mt-1">{products.length} SKUs</div>
        </div>
        <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-xl">
          <div className="text-xs text-slate-400 font-medium">Valoración Total Inventario</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {formatCOP(products.reduce((acc, p) => acc + p.cost * p.stock, 0))}
          </div>
        </div>
        <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-xl">
          <div className="text-xs text-slate-400 font-medium">Alertas Stock Mínimo</div>
          <div className="text-2xl font-bold text-amber-400 mt-1 flex items-center gap-2">
            {lowStockCount} {lowStockCount > 0 && <AlertTriangle className="w-5 h-5 text-amber-400" />}
          </div>
        </div>
        <div className="bg-slate-800/80 border border-slate-700 p-4 rounded-xl">
          <div className="text-xs text-slate-400 font-medium">Margen Promedio</div>
          <div className="text-2xl font-bold text-sky-400 mt-1">32.4%</div>
        </div>
      </div>

      {/* Table Card */}
      <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-3">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Package className="w-5 h-5 text-emerald-400" />
            Catálogo y Control de Inventario
          </h2>
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar por SKU o descripción..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs placeholder-slate-400 focus:outline-none focus:border-emerald-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-700">
              <tr>
                <th className="p-3">SKU</th>
                <th className="p-3">Descripción Producto</th>
                <th className="p-3">Categoría</th>
                <th className="p-3 text-right">Costo (PUC 1435)</th>
                <th className="p-3 text-right">Precio Venta</th>
                <th className="p-3 text-center">IVA</th>
                <th className="p-3 text-center">Stock Actual</th>
                <th className="p-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60">
              {filtered.map((product) => {
                const isLow = product.stock <= product.minStock;
                const isEditing = editingId === product.id;
                const imgUrl =
                  images.find((img) => img.productId === product.id && (img.isPrimary || img.imageType === 'PRIMARY'))?.url ||
                  images.find((img) => img.productId === product.id)?.url ||
                  product.image;
                return (
                  <tr key={product.id} className="hover:bg-slate-700/30 transition">
                    <td className="p-3 font-mono font-bold text-slate-400">{product.sku}</td>
                    <td className="p-3 font-medium text-white">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-700 overflow-hidden shrink-0 flex items-center justify-center">
                          {imgUrl ? (
                            <img
                              src={imgUrl}
                              alt={product.name}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                          ) : (
                            <Package className="w-3.5 h-3.5 text-slate-600" />
                          )}
                        </div>
                        <span>{product.name}</span>
                      </div>
                    </td>
                    <td className="p-3">
                      <span className="bg-slate-700 text-slate-300 px-2 py-0.5 rounded text-[11px]">
                        {product.category}
                      </span>
                    </td>
                    <td className="p-3 text-right font-mono text-slate-400">{formatCOP(product.cost)}</td>
                    <td className="p-3 text-right font-mono font-semibold text-emerald-400">{formatCOP(product.price)}</td>
                    <td className="p-3 text-center">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${product.ivaRate > 0 ? 'bg-indigo-500/20 text-indigo-300' : 'bg-emerald-500/20 text-emerald-300'}`}>
                        {product.ivaRate > 0 ? '19%' : '0% Exento'}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      {isEditing ? (
                        <div className="flex items-center justify-center gap-1">
                          <input
                            type="number"
                            value={newStockVal}
                            onChange={(e) => setNewStockVal(parseInt(e.target.value) || 0)}
                            className="w-16 bg-slate-900 border border-emerald-500 rounded px-1.5 py-0.5 text-center text-white"
                          />
                          <button
                            onClick={() => handleSaveStock(product.id)}
                            className="p-1 text-emerald-400 hover:text-emerald-300"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </button>
                        </div>
                      ) : (
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-mono font-bold ${isLow ? 'bg-red-500/20 text-red-300 border border-red-500/30' : 'text-slate-300'}`}>
                          {isLow && <AlertTriangle className="w-3 h-3 text-red-400" />}
                          {product.stock} unids
                        </span>
                      )}
                    </td>
                    <td className="p-3 text-center">
                      <button
                        onClick={() => {
                          setEditingId(product.id);
                          setNewStockVal(product.stock);
                        }}
                        className="text-xs text-sky-400 hover:underline inline-flex items-center gap-1"
                      >
                        <Edit2 className="w-3 h-3" /> Ajustar Stock
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default InventoryManager;
