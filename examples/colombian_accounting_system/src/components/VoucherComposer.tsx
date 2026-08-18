import React, { useState } from 'react';
import { AccountingEntryLine, VoucherType } from '../types/accounting';
import { PUC_CATALOG } from '../constants/pucColombia';
import { useAccountingStore } from '../store/accountingStore';
import { useAuthStore } from '../store/authStore';
import { Button } from '../atoms/Button';
import { Badge } from '../atoms/Badge';
import { formatCop } from '../utils/mathPrecision';
import { Trash2, CheckCircle2, AlertTriangle, Plus } from 'lucide-react';

interface VoucherComposerProps {
  prefilledLines?: AccountingEntryLine[];
}

export const VoucherComposer: React.FC<VoucherComposerProps> = ({ prefilledLines = [] }) => {
  const { addVoucher, activePeriod, lockedPeriods } = useAccountingStore();
  const { currentUser } = useAuthStore();

  const [voucherType, setVoucherType] = useState<VoucherType>('FACTURA_VENTA');
  const [notes, setNotes] = useState('Contabilización de operación mercantil');
  const [lines, setLines] = useState<AccountingEntryLine[]>([
    { id: '1', accountCode: '11050501', accountName: 'Caja Principal Moneda Nacional', thirdPartyNit: '900.123.456-1', thirdPartyName: 'Distribuidora Andina SAS', concept: 'Cobro de factura', debit: 1000000, credit: 0 },
    { id: '2', accountCode: '13050501', accountName: 'Cartera Clientes Comerciales', thirdPartyNit: '900.123.456-1', thirdPartyName: 'Distribuidora Andina SAS', concept: 'Cancelación saldo', debit: 0, credit: 1000000 },
  ]);
  const [feedback, setFeedback] = useState<{ msg: string; type: 'error' | 'success' } | null>(null);

  const totalDebits = lines.reduce((sum, l) => sum + Number(l.debit || 0), 0);
  const totalCredits = lines.reduce((sum, l) => sum + Number(l.credit || 0), 0);
  const difference = Math.abs(totalDebits - totalCredits);
  const isBalanced = difference < 0.001 && totalDebits > 0;

  const handleAddLine = () => {
    const defaultAccount = PUC_CATALOG.find((p) => p.acceptsMovement) || PUC_CATALOG[4];
    setLines([
      ...lines,
      {
        id: Math.random().toString(),
        accountCode: defaultAccount.code,
        accountName: defaultAccount.name,
        thirdPartyNit: currentUser.companyNit,
        thirdPartyName: currentUser.companyName,
        concept: notes,
        debit: 0,
        credit: 0,
      },
    ]);
  };

  const handleRemoveLine = (id: string) => {
    setLines(lines.filter((l) => l.id !== id));
  };

  const handleSave = () => {
    if (!isBalanced) {
      setFeedback({ msg: 'Partida doble descuadrada. Débitos y Créditos deben coincidir.', type: 'error' });
      return;
    }
    const res = addVoucher({
      id: 'V-' + Date.now(),
      consecutive: `COMP-${Date.now().toString().slice(-4)}`,
      type: voucherType,
      date: new Date().toISOString().split('T')[0],
      period: activePeriod,
      notes,
      lines,
      status: currentUser.role === 'ADMIN' || currentUser.role === 'CONTADOR' ? 'CONTABILIZADO' : 'BORRADOR',
      createdBy: `${currentUser.name} (${currentUser.role})`,
      createdAt: new Date().toISOString().replace('T', ' ').slice(0, 19),
      isLocked: lockedPeriods.includes(activePeriod),
    });

    if (res.success) {
      setFeedback({ msg: 'Comprobante registrado y asentado en libros correctamente.', type: 'success' });
    } else {
      setFeedback({ msg: res.error || 'Error registrando comprobante', type: 'error' });
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <h2 className="text-base font-semibold text-slate-100">Registro de Comprobante / Asiento Doble Partida</h2>
          <p className="text-xs text-slate-400">Validación matemática en tiempo real según Decreto 2420/2015</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={voucherType}
            onChange={(e) => setVoucherType(e.target.value as VoucherType)}
            className="bg-slate-950 border border-slate-700 text-xs rounded px-3 py-1.5 text-slate-200 font-mono"
          >
            <option value="FACTURA_VENTA">Factura Electrónica de Venta</option>
            <option value="COMPROBANTE_INGRESO">Recibo de Caja / Ingreso</option>
            <option value="COMPROBANTE_EGRESO">Comprobante de Egreso / Pago</option>
            <option value="NOTA_CONTABLE">Nota Contable de Ajuste</option>
          </select>
          <Button size="sm" onClick={handleAddLine} variant="secondary" className="gap-1">
            <Plus className="w-3.5 h-3.5" /> Fila
          </Button>
        </div>
      </div>

      {feedback && (
        <div className={`p-3 rounded-lg text-xs font-mono border ${feedback.type === 'error' ? 'bg-rose-950/70 border-rose-800 text-rose-300' : 'bg-emerald-950/70 border-emerald-800 text-emerald-300'}`}>
          {feedback.msg}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse font-mono">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/40">
              <th className="py-2 px-2">Cuenta PUC</th>
              <th className="py-2 px-2">Tercero (NIT - Razón)</th>
              <th className="py-2 px-2">Concepto</th>
              <th className="py-2 px-2 text-right">Débito</th>
              <th className="py-2 px-2 text-right">Crédito</th>
              <th className="py-2 px-2 text-center">Acción</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {lines.map((l, idx) => (
              <tr key={l.id} className="hover:bg-slate-800/30">
                <td className="py-1.5 px-2">
                  <select
                    value={l.accountCode}
                    onChange={(e) => {
                      const sel = PUC_CATALOG.find((p) => p.code === e.target.value);
                      const copy = [...lines];
                      copy[idx].accountCode = e.target.value;
                      if (sel) copy[idx].accountName = sel.name;
                      setLines(copy);
                    }}
                    className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs w-52"
                  >
                    {PUC_CATALOG.filter((p) => p.acceptsMovement).map((p) => (
                      <option key={p.code} value={p.code}>
                        {p.code} - {p.name}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="py-1.5 px-2">
                  <input
                    type="text"
                    value={l.thirdPartyNit}
                    onChange={(e) => {
                      const copy = [...lines];
                      copy[idx].thirdPartyNit = e.target.value;
                      setLines(copy);
                    }}
                    placeholder="NIT"
                    className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs w-28"
                  />
                </td>
                <td className="py-1.5 px-2">
                  <input
                    type="text"
                    value={l.concept}
                    onChange={(e) => {
                      const copy = [...lines];
                      copy[idx].concept = e.target.value;
                      setLines(copy);
                    }}
                    className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs w-full"
                  />
                </td>
                <td className="py-1.5 px-2">
                  <input
                    type="number"
                    value={l.debit || ''}
                    onChange={(e) => {
                      const copy = [...lines];
                      copy[idx].debit = Number(e.target.value) || 0;
                      setLines(copy);
                    }}
                    className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-right text-emerald-400 font-semibold text-xs w-28"
                  />
                </td>
                <td className="py-1.5 px-2">
                  <input
                    type="number"
                    value={l.credit || ''}
                    onChange={(e) => {
                      const copy = [...lines];
                      copy[idx].credit = Number(e.target.value) || 0;
                      setLines(copy);
                    }}
                    className="bg-slate-950 border border-slate-700 rounded px-2 py-1 text-right text-sky-400 font-semibold text-xs w-28"
                  />
                </td>
                <td className="py-1.5 px-2 text-center">
                  <button onClick={() => handleRemoveLine(l.id)} className="text-slate-500 hover:text-rose-400 p-1">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-slate-700 font-bold bg-slate-950/60">
              <td colSpan={3} className="py-2 px-2 text-right text-slate-300">SUMAS IGUALES:</td>
              <td className="py-2 px-2 text-right text-emerald-400">{formatCop(totalDebits)}</td>
              <td className="py-2 px-2 text-right text-sky-400">{formatCop(totalCredits)}</td>
              <td className="py-2 px-2 text-center">
                {isBalanced ? (
                  <Badge variant="success"><CheckCircle2 className="w-3 h-3 mr-1 inline" />CUADRADO</Badge>
                ) : (
                  <Badge variant="danger"><AlertTriangle className="w-3 h-3 mr-1 inline" />DESCUADRE</Badge>
                )}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="flex items-center justify-between pt-2">
        <span className="text-xs text-slate-400 font-mono">
          Diferencia: <strong className={difference === 0 ? 'text-emerald-400' : 'text-rose-400'}>{formatCop(difference)}</strong>
        </span>
        <Button onClick={handleSave} disabled={!isBalanced || currentUser.role === 'AUDITOR'}>
          Asentar Comprobante Contable
        </Button>
      </div>
    </div>
  );
};