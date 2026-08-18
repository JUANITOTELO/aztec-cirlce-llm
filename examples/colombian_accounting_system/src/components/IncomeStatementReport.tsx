import React from 'react';
import { generateIncomeStatement } from '../engine/financialStatements';
import { useAccountingStore } from '../store/accountingStore';
import { formatCop } from '../utils/mathPrecision';
import { TrendingUp, PieChart } from 'lucide-react';

export const IncomeStatementReport: React.FC = () => {
  const { vouchers, activePeriod } = useAccountingStore();
  const report = generateIncomeStatement(vouchers, activePeriod);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-emerald-400" />
          <h3 className="font-semibold text-slate-100 text-sm">Estado de Resultados Integral (Pérdidas y Ganancias - P&G)</h3>
        </div>
        <span className="text-xs text-slate-400 font-mono">Bajo NIIF / COLGAAP</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <span className="text-[11px] text-slate-400 block">Ingresos Operacionales (Clase 4)</span>
          <span className="text-emerald-400 font-mono font-bold text-base">{formatCop(report.grossRevenue)}</span>
        </div>
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <span className="text-[11px] text-slate-400 block">Costos de Ventas (Clase 6)</span>
          <span className="text-rose-400 font-mono font-bold text-base">{formatCop(report.costOfSales)}</span>
        </div>
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <span className="text-[11px] text-slate-400 block">Gastos Operacionales (Clase 5)</span>
          <span className="text-amber-400 font-mono font-bold text-base">{formatCop(report.operatingExpenses)}</span>
        </div>
      </div>

      <div className="bg-emerald-950/30 border border-emerald-800/50 p-4 rounded-lg flex items-center justify-between">
        <div>
          <div className="text-xs text-emerald-300 font-medium uppercase tracking-wider">Utilidad Neta del Ejercicio (Antes de Impuestos)</div>
          <div className="text-xs text-slate-400">Fórmula: Ingresos - Costos - Gastos Operacionales</div>
        </div>
        <div className="text-xl font-bold font-mono text-emerald-400">
          {formatCop(report.netOperatingIncome)}
        </div>
      </div>
    </div>
  );
};