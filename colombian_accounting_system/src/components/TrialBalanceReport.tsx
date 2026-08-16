import React from 'react';
import { calculateTrialBalance } from '../engine/balanceCalculator';
import { useAccountingStore } from '../store/accountingStore';
import { formatCop } from '../utils/mathPrecision';
import { Badge } from '../atoms/Badge';
import { FileSpreadsheet, Download } from 'lucide-react';
import { Button } from '../atoms/Button';

export const TrialBalanceReport: React.FC = () => {
  const { vouchers, activePeriod } = useAccountingStore();
  const rows = calculateTrialBalance(vouchers, activePeriod);

  const totalDebits = rows.filter(r => r.level === 'CLASE').reduce((s, r) => s + r.debits, 0);
  const totalCredits = rows.filter(r => r.level === 'CLASE').reduce((s, r) => s + r.credits, 0);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-3 gap-2">
        <div>
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            <h3 className="font-semibold text-slate-100 text-sm">Balance de Prueba (Trial Balance)</h3>
          </div>
          <p className="text-xs text-slate-400">Periodo Contable: <span className="font-mono text-emerald-400 font-semibold">{activePeriod}</span></p>
        </div>
        <Button size="sm" variant="secondary" className="gap-1.5">
          <Download className="w-3.5 h-3.5" /> Exportar Exógena
        </Button>
      </div>

      <div className="max-h-[380px] overflow-y-auto border border-slate-800 rounded-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-950 sticky top-0 border-b border-slate-800 text-slate-400">
            <tr>
              <th className="py-2 px-3">Código PUC</th>
              <th className="py-2 px-3">Nombre de Cuenta</th>
              <th className="py-2 px-3 text-right">Débitos</th>
              <th className="py-2 px-3 text-right">Créditos</th>
              <th className="py-2 px-3 text-right">Saldo Final</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {rows.map((row) => {
              const isHeader = row.level === 'CLASE' || row.level === 'GRUPO';
              return (
                <tr key={row.code} className={isHeader ? 'bg-slate-950/70 font-semibold text-slate-200' : 'hover:bg-slate-800/30 text-slate-300'}>
                  <td className="py-1.5 px-3 text-emerald-400">{row.code}</td>
                  <td className="py-1.5 px-3" style={{ paddingLeft: `${Math.max(12, row.code.length * 6)}px` }}>
                    {row.name}
                  </td>
                  <td className="py-1.5 px-3 text-right text-emerald-400">{formatCop(row.debits)}</td>
                  <td className="py-1.5 px-3 text-right text-sky-400">{formatCop(row.credits)}</td>
                  <td className="py-1.5 px-3 text-right font-bold text-slate-100">{formatCop(row.finalBalance)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};