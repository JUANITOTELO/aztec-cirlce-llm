import React from 'react';
import { useAccountingStore } from '../store/accountingStore';
import { useAuthStore } from '../store/authStore';
import { Badge } from '../atoms/Badge';
import { Button } from '../atoms/Button';
import { VoucherStatus } from '../types/accounting';
import { Check, FileText } from 'lucide-react';

export const VoucherHistoryTable: React.FC = () => {
  const { vouchers, updateVoucherStatus } = useAccountingStore();
  const { currentUser } = useAuthStore();

  const getBadgeVariant = (status: VoucherStatus) => {
    switch (status) {
      case 'CONTABILIZADO': return 'success';
      case 'APROBADO': return 'info';
      case 'REVISADO': return 'warning';
      default: return 'neutral';
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2 font-semibold text-slate-100 text-sm">
          <FileText className="w-4 h-4 text-emerald-400" />
          <span>Libro Diario de Comprobantes Contables</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
            <tr>
              <th className="py-2 px-3">Consecutivo</th>
              <th className="py-2 px-3">Fecha</th>
              <th className="py-2 px-3">Periodo</th>
              <th className="py-2 px-3">Tipo</th>
              <th className="py-2 px-3">Elaborado Por</th>
              <th className="py-2 px-3 text-center">Estado</th>
              <th className="py-2 px-3 text-center">Gobernanza RBAC</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {vouchers.map((v) => (
              <tr key={v.id} className="hover:bg-slate-800/30">
                <td className="py-2.5 px-3 font-semibold text-emerald-400">{v.consecutive}</td>
                <td className="py-2.5 px-3 text-slate-300">{v.date}</td>
                <td className="py-2.5 px-3 text-slate-400">{v.period}</td>
                <td className="py-2.5 px-3 text-slate-200">{v.type}</td>
                <td className="py-2.5 px-3 text-slate-400">{v.createdBy}</td>
                <td className="py-2.5 px-3 text-center">
                  <Badge variant={getBadgeVariant(v.status)}>{v.status}</Badge>
                </td>
                <td className="py-2.5 px-3 text-center">
                  {v.status === 'BORRADOR' && (currentUser.role === 'CONTADOR' || currentUser.role === 'ADMIN') && (
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => updateVoucherStatus(v.id, 'CONTABILIZADO', currentUser.id)}
                      className="gap-1 text-[11px] py-0.5 px-2"
                    >
                      <Check className="w-3 h-3" /> Aprobar y Asentar
                    </Button>
                  )}
                  {v.status === 'CONTABILIZADO' && (
                    <span className="text-slate-500 text-[11px]">Asentado en Firme</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};