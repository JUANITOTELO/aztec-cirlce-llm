import React, { useState } from 'react';
import { Product } from '../../types/store';
import { StockAdjustmentPayload, AdjustmentType, AdjustmentReason } from '../../types/product';
import { formatCOP } from '../../utils/formatters';
import { X, Layers, AlertCircle } from 'lucide-react';

interface Props {
  isOpen: boolean;
  product: Product | null;
  currentUserName: string;
  onClose: () => void;
  onConfirm: (payload: StockAdjustmentPayload) => void;
}

export const ProductStockAdjustModal: React.FC<Props> = ({ isOpen, product, currentUserName, onClose, onConfirm }) => {
  const [adjustmentType, setAdjustmentType] = useState<AdjustmentType>('ADD');
  const [quantity, setQuantity] = useState<number>(1);
  const [reason, setReason] = useState<AdjustmentReason>('COMPRA_PROVEEDOR');
  const [notes, setNotes] = useState('');

  if (!isOpen || !product) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (quantity <= 0) return;

    const payload: StockAdjustmentPayload = {
      id: `adj-${Date.now()}`,
      productId: product.id,
      sku: product.sku,
      productName: product.name,
      adjustmentType,
      quantity,
      unitCost: product.cost,
      reason,
      notes,
      adjustedBy: currentUserName || 'Admin',
      adjustedAt: new Date().toISOString(),
    };
    onConfirm(payload);
    onClose();
  };

  const projectedStock = adjustmentType === 'ADD' ? product.stock + quantity : Math.max(0, product.stock - quantity);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md border border-slate-700 overflow-hidden animate-in fade-in duration-200">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-700/80 bg-slate-850">
          <h3 className="font-bold text-white flex items-center gap-2">
            <Layers className="w-5 h-5 text-emerald-400" />
            Ajuste de Stock
          </h3>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="bg-slate-900/80 border border-slate-700/60 p-3.5 rounded-xl text-sm">
            <p className="font-semibold text-white">{product.name}</p>
            <p className="text-xs text-slate-400 mt-0.5">
              SKU: <span className="font-mono text-slate-300">{product.sku}</span> | Stock Actual: <span className="font-bold text-emerald-400">{product.stock} un.</span>
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => { setAdjustmentType('ADD'); setReason('COMPRA_PROVEEDOR'); }}
              className={`py-2.5 px-3 text-xs font-semibold rounded-xl border transition-colors ${
                adjustmentType === 'ADD'
                  ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300 shadow-sm'
                  : 'bg-slate-900/40 border-slate-700 text-slate-400 hover:text-slate-200'
              }`}
            >
              + Entrada (Aumentar)
            </button>
            <button
              type="button"
              onClick={() => { setAdjustmentType('REMOVE'); setReason('MERMA_DETERIORO'); }}
              className={`py-2.5 px-3 text-xs font-semibold rounded-xl border transition-colors ${
                adjustmentType === 'REMOVE'
                  ? 'bg-rose-500/20 border-rose-500 text-rose-300 shadow-sm'
                  : 'bg-slate-900/40 border-slate-700 text-slate-400 hover:text-slate-200'
              }`}
            >
              - Salida (Disminuir)
            </button>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Cantidad a Ajustar</label>
            <input
              type="number"
              min="1"
              value={quantity}
              onChange={e => setQuantity(Math.max(1, Number(e.target.value)))}
              className="w-full px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 text-white rounded-xl text-sm font-mono focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              required
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Motivo Contable</label>
            <select
              value={reason}
              onChange={e => setReason(e.target.value as AdjustmentReason)}
              className="w-full px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 text-white rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              {adjustmentType === 'ADD' ? (
                <>
                  <option value="COMPRA_PROVEEDOR" className="bg-slate-900 text-white">Compra a Proveedor (PUC 2205)</option>
                  <option value="AJUSTE_INVENTARIO" className="bg-slate-900 text-white">Ajuste de Conteo Físico</option>
                  <option value="DEVOLUCION_CLIENTE" className="bg-slate-900 text-white">Devolución de Cliente</option>
                </>
              ) : (
                <>
                  <option value="MERMA_DETERIORO" className="bg-slate-900 text-white">Merma / Avería / Vencimiento (PUC 5315)</option>
                  <option value="AJUSTE_INVENTARIO" className="bg-slate-900 text-white">Faltante en Inventario</option>
                  <option value="AUTOCONSUMO" className="bg-slate-900 text-white">Autoconsumo Operativo</option>
                </>
              )}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">Observaciones / Documento Soporte</label>
            <input
              type="text"
              value={notes}
              onChange={e => setNotes(e.target.value)}
              placeholder="Ej: Factura compra F-1029"
              className="w-full px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 text-white placeholder-slate-500 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            />
          </div>
          <div className="p-3.5 bg-slate-900/70 border border-slate-700/60 rounded-xl text-xs flex justify-between items-center text-slate-300">
            <span>Stock Proyectado: <strong className="text-emerald-400 font-mono text-sm">{projectedStock} un.</strong></span>
            <span>Impacto: <strong className="text-white font-mono">{formatCOP(quantity * product.cost)}</strong></span>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 bg-slate-700/50 hover:bg-slate-700 text-slate-300 border border-slate-600 rounded-xl text-sm font-medium transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-emerald-900/30 transition-colors"
            >
              Confirmar Ajuste
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
