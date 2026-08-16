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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col border border-slate-700 overflow-hidden animate-in fade-in duration-200">
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-700/80 bg-slate-850">
          <h3 className="font-bold text-white flex items-center gap-2">
            <History className="w-5 h-5 text-emerald-400" />
            Historial Auditoría de Precios
          </h3>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <div className="p-6 overflow-y-auto flex-1">
          {records.length === 0 ? (
            <p className="text-center text-sm text-slate-400 py-10">No hay registros de modificaciones de precios para esta sesión.</p>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-slate-700/60 bg-slate-900/50">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-700/80 bg-slate-900 text-slate-400 uppercase tracking-wider text-[11px]">
                    <th className="py-3 px-4">Fecha/Hora</th>
                    <th className="py-3 px-4">SKU</th>
                    <th className="py-3 px-4">Precio Ant. &rarr; Nuevo</th>
                    <th className="py-3 px-4">Costo Ant. &rarr; Nuevo</th>
                    <th className="py-3 px-4">IVA</th>
                    <th className="py-3 px-4">Usuario</th>
                    <th className="py-3 px-4">Motivo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {records.map(rec => (
                    <tr key={rec.id} className="hover:bg-slate-800/60 transition-colors">
                      <td className="py-3 px-4 text-slate-400 whitespace-nowrap">{new Date(rec.changedAt).toLocaleString()}</td>
                      <td className="py-3 px-4 font-mono font-semibold text-slate-200">{rec.sku}</td>
                      <td className="py-3 px-4 font-mono"><span className="line-through text-slate-500">{formatCOP(rec.oldPrice)}</span> &rarr; <span className="font-bold text-emerald-400">{formatCOP(rec.newPrice)}</span></td>
                      <td className="py-3 px-4 font-mono"><span className="line-through text-slate-500">{formatCOP(rec.oldCost)}</span> &rarr; <span className="font-semibold text-cyan-400">{formatCOP(rec.newCost)}</span></td>
                      <td className="py-3 px-4 text-slate-300 font-mono">{formatPercent(rec.newIvaRate ?? 0.19)}</td>
                      <td className="py-3 px-4 text-slate-200">{rec.changedBy}</td>
                      <td className="py-3 px-4 text-slate-400">{rec.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
        <div className="px-6 py-4 border-t border-slate-700/80 bg-slate-850 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-slate-700/60 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded-xl text-sm font-medium transition-colors"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};
