import React from 'react';
import { LedgerEntry } from '../../types/store';
import { formatCOP } from '../../utils/formatters';
import { BookOpen, CheckCircle, Scale, ShieldCheck } from 'lucide-react';

interface LedgerJournalProps {
  entries?: LedgerEntry[];
  ledgerEntries?: LedgerEntry[];
  setLedgerEntries?: React.Dispatch<React.SetStateAction<LedgerEntry[]>>;
}

export const LedgerJournal: React.FC<LedgerJournalProps> = ({ entries, ledgerEntries }) => {
  const actualEntries = entries || ledgerEntries || [];
  const totalDebits = actualEntries.reduce((s, e) => s + e.debit, 0);
  const totalCredits = actualEntries.reduce((s, e) => s + e.credit, 0);
  const isBalanced = totalDebits === totalCredits;

  return (
    <div className="space-y-6">
      {/* Balance Summary Header */}
      <div className="bg-slate-800/90 border border-slate-700 p-5 rounded-xl flex flex-wrap items-center justify-between gap-4 shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-indigo-600/20 text-indigo-400 flex items-center justify-center border border-indigo-500/30">
            <Scale className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              Libro Diario &amp; Mayor (Partida Doble)
            </h2>
            <p className="text-xs text-slate-400">
              Validación continua de ecuación contable: Activo = Pasivo + Patrimonio
            </p>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="text-right">
            <span className="text-xs text-slate-400 block">Total Débitos</span>
            <span className="font-mono text-base font-bold text-emerald-400">{formatCOP(totalDebits)}</span>
          </div>
          <div className="text-right">
            <span className="text-xs text-slate-400 block">Total Créditos</span>
            <span className="font-mono text-base font-bold text-sky-400">{formatCOP(totalCredits)}</span>
          </div>
          <div className={`px-3 py-1.5 rounded-lg border flex items-center gap-1.5 text-xs font-bold ${
            isBalanced
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
              : 'bg-red-500/20 text-red-300 border-red-500/30'
          }`}>
            {isBalanced ? (
              <>
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                Balance Cuadrado
              </>
            ) : (
              'Descuadre Detectado'
            )}
          </div>
        </div>
      </div>

      {/* Journal Table */}
      <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-700">
              <tr>
                <th className="p-3">Ref / TxID</th>
                <th className="p-3">Fecha</th>
                <th className="p-3">Código PUC</th>
                <th className="p-3">Nombre Cuenta PUC</th>
                <th className="p-3">Descripción Asiento</th>
                <th className="p-3 text-right text-emerald-400">Débito ($)</th>
                <th className="p-3 text-right text-sky-400">Crédito ($)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60 font-mono">
              {actualEntries.map((e) => (
                <tr key={e.id} className="hover:bg-slate-700/30 transition">
                  <td className="p-3 text-slate-400 font-bold">{e.transactionId}</td>
                  <td className="p-3 text-slate-400 font-sans">{e.date}</td>
                  <td className="p-3 text-indigo-400 font-bold">{e.pucCode}</td>
                  <td className="p-3 text-slate-200 font-sans font-medium">{e.pucName}</td>
                  <td className="p-3 text-slate-400 font-sans text-xs">{e.description}</td>
                  <td className="p-3 text-right text-emerald-400 font-semibold">
                    {e.debit > 0 ? formatCOP(e.debit) : '-'}
                  </td>
                  <td className="p-3 text-right text-sky-400 font-semibold">
                    {e.credit > 0 ? formatCOP(e.credit) : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="bg-slate-900/90 font-bold border-t-2 border-slate-600 font-mono">
              <tr>
                <td colSpan={5} className="p-3 text-right text-slate-300 font-sans">
                  SUMAS IGUALES:
                </td>
                <td className="p-3 text-right text-emerald-400 text-sm">{formatCOP(totalDebits)}</td>
                <td className="p-3 text-right text-sky-400 text-sm">{formatCOP(totalCredits)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LedgerJournal;
