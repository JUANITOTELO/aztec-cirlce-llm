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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-md border border-slate-200 dark:border-slate-700">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2"><Layers className="w-5 h-5 text-blue-600" /> Ajuste de Stock</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="bg-slate-50 dark:bg-slate-700/50 p-3 rounded-lg text-sm">
            <p className="font-semibold text-slate-800 dark:text-white">{product.name}</p>
            <p className="text-xs text-slate-500">SKU: {product.sku} | Stock Actual: <span className="font-bold text-blue-600">{product.stock}</span></p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <button type="button" onClick={() => { setAdjustmentType('ADD'); setReason('COMPRA_PROVEEDOR'); }} className={`py-2 text-sm font-medium rounded-lg border ${adjustmentType === 'ADD' ? 'bg-emerald-50 border-emerald-500 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300' : 'border-slate-200'}`}>+ Entrada (Aumentar)</button>
            <button type="button" onClick={() => { setAdjustmentType('REMOVE'); setReason('MERMA_DETERIORO'); }} className={`py-2 text-sm font-medium rounded-lg border ${adjustmentType === 'REMOVE' ? 'bg-red-50 border-red-500 text-red-700 dark:bg-red-950/40 dark:text-red-300' : 'border-slate-200'}`}>- Salida (Disminuir)</button>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Cantidad a Ajustar</label>
            <input type="number" min="1" value={quantity} onChange={e => setQuantity(Math.max(1, Number(e.target.value)))} className="w-full text-sm border rounded-lg p-2.5 dark:bg-slate-700 dark:text-white" required />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Motivo Contable</label>
            <select value={reason} onChange={e => setReason(e.target.value as AdjustmentReason)} className="w-full text-sm border rounded-lg p-2.5 dark:bg-slate-700 dark:text-white">
              {adjustmentType === 'ADD' ? (
                <><option value="COMPRA_PROVEEDOR">Compra a Proveedor (PUC 2205)</option><option value="AJUSTE_INVENTARIO">Ajuste de Conteo Físico</option><option value="DEVOLUCION_CLIENTE">Devolución de Cliente</option></>
              ) : (
                <><option value="MERMA_DETERIORO">Merma / Avería / Vencimiento (PUC 5315)</option><option value="AJUSTE_INVENTARIO">Faltante en Inventario</option><option value="AUTOCONSUMO">Autoconsumo Operativo</option></>
              )}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-600 dark:text-slate-300 mb-1">Observaciones / Documento Soporte</label>
            <input type="text" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Ej: Factura compra F-1029" className="w-full text-sm border rounded-lg p-2.5 dark:bg-slate-700 dark:text-white" />
          </div>
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-xs flex justify-between text-blue-900 dark:text-blue-300 font-medium">
            <span>Stock Proyectado: <strong>{projectedStock}</strong></span>
            <span>Impacto Contable: <strong>{formatCOP(quantity * product.cost)}</strong></span>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg">Cancelar</button>
            <button type="submit" className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium">Confirmar Ajuste</button>
          </div>
        </form>
      </div>
    </div>
  );
};
