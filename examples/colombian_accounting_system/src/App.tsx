import React, { useState } from 'react';
import { Header } from './components/Header';
import { TaxCalculatorPanel } from './components/TaxCalculatorPanel';
import { VoucherComposer } from './components/VoucherComposer';
import { PucExplorer } from './components/PucExplorer';
import { TrialBalanceReport } from './components/TrialBalanceReport';
import { IncomeStatementReport } from './components/IncomeStatementReport';
import { VoucherHistoryTable } from './components/VoucherHistoryTable';
import { BookOpen, Calculator, FileSpreadsheet, TrendingUp, History, PenTool } from 'lucide-react';

type ActiveTab = 'vouchers' | 'taxes' | 'puc' | 'trial_balance' | 'income_statement' | 'history';

export default function App() {
  const [tab, setTab] = useState<ActiveTab>('vouchers');

  const tabs = [
    { id: 'vouchers', label: 'Comprobantes & Asientos', icon: PenTool },
    { id: 'taxes', label: 'Liquidación DIAN', icon: Calculator },
    { id: 'puc', label: 'Catálogo PUC', icon: BookOpen },
    { id: 'trial_balance', label: 'Balance de Prueba', icon: FileSpreadsheet },
    { id: 'income_statement', label: 'P&G (Resultados)', icon: TrendingUp },
    { id: 'history', label: 'Historial / Auditoría', icon: History },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Header />

      <div className="bg-slate-900/50 border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-6 flex space-x-2 overflow-x-auto">
          {tabs.map((t) => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id as ActiveTab)}
                className={`flex items-center gap-2 py-3 px-4 text-xs font-medium border-b-2 transition-all ${
                  active
                    ? 'border-emerald-500 text-emerald-400 bg-slate-800/40'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <Icon className="w-4 h-4" />
                {t.label}
              </button>
            );
          })}
        </div>
      </div>

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {tab === 'vouchers' && (
          <div className="space-y-6">
            <TaxCalculatorPanel />
            <VoucherComposer />
          </div>
        )}
        {tab === 'taxes' && <TaxCalculatorPanel />}
        {tab === 'puc' && <PucExplorer />}
        {tab === 'trial_balance' && <TrialBalanceReport />}
        {tab === 'income_statement' && <IncomeStatementReport />}
        {tab === 'history' && <VoucherHistoryTable />}
      </main>
    </div>
  );
}