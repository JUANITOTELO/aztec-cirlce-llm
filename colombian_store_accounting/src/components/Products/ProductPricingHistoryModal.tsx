import React from 'react';
import { ProductPricingRecord } from '../../types/product';
import { formatCOP, formatPercent } from '../../utils/formatters';
import { X, History } from 'lucide-react';

interface Props {
  isOpen: boolean;
  records: ProductPricingRecord[];
  onClose: () => void;
}

export const ProductPricingHistoryModal: React.FC<Props> = ({ isOpen, records, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-xl w-full max-w-3xl max-h-[85vh] flex flex-col border border-slate-200 dark:border-slate-700">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-200 dark:border-slate-700">
          <h3 className="font-bold text-slate-800 dark:text-white flex items-center gap-2"><History className="w-5 h-5 text-blue-600" /> Historial Auditoría de Precios</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-6 overflow-y-auto flex-1">
          {records.length === 0 ? (
            <p className="text-center text-sm text-slate-500 py-8">No hay registros de modificaciones de precios para esta sesión.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700 text-slate-500 uppercase tracking-wider">
                    <th className="py-2 px-3">Fecha/Hora</th>
                    <th className="py-2 px-3">SKU</th>
                    <th className="py-2 px-3">Precio Ant. &rarr; Nuevo</th>
                    <th className="py-2 px-3">Costo Ant. &rarr; Nuevo</th>
                    <th className="py-2 px-3">IVA</th>
                    <th className="py-2 px-3">Usuario</th>
                    <th className="py-2 px-3">Motivo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {records.map(rec => (
                    <tr key={rec.id} className="hover:bg-slate-50 dark:hover:bg-slate-700/40">
                      <td className="py-2 px-3 text-slate-500 whitespace-nowrap">{new Date(rec.changedAt).toLocaleString()}</td>
                      <td className="py-2 px-3 font-semibold text-slate-700 dark:text-slate-300">{rec.sku}</td>
                      <td className="py-2 px-3"><span className="line-through text-slate-400">{formatCOP(rec.oldPrice)}</span> &rarr; <span className="font-bold text-emerald-600">{formatCOP(rec.newPrice)}</span></td>
                      <td className="py-2 px-3"><span className="line-through text-slate-400">{formatCOP(rec.oldCost)}</span> &rarr; <span className="font-semibold text-blue-600">{formatCOP(rec.newCost)}</span></td>
                      <td className="py-2 px-3 text-slate-600 dark:text-slate-300">{formatPercent(rec.newIvaRate ?? 0.19)}</td>
                      <td className="py-2 px-3 text-slate-700 dark:text-slate-200">{rec.changedBy}</td>
                      <td className="py-2 px-3 text-slate-500">{rec.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div className="px-6 py-3 border-t border-slate-200 dark:border-slate-700 flex justify-end">
          <button onClick={onClose} className="px-4 py-2 bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium">Cerrar</button>
        </div>
      </div>
    </div>
  );
};
