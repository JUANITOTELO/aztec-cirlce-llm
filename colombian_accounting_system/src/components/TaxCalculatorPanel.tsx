import React, { useState } from 'react';
import { settleDianTaxes } from '../engine/taxSettlementEngine';
import { formatCop } from '../utils/mathPrecision';
import { Button } from '../atoms/Button';
import { Calculator, PlusCircle } from 'lucide-react';

interface TaxCalculatorProps {
  onAddVoucherLineFromTax?: (lines: any[]) => void;
}

export const TaxCalculatorPanel: React.FC<TaxCalculatorProps> = ({ onAddVoucherLineFromTax }) => {
  const [subtotal, setSubtotal] = useState<number>(5000000);
  const [ivaRate, setIvaRate] = useState<number>(19);
  const [reteFuenteRate, setReteFuenteRate] = useState<number>(2.5);
  const [reteIcaPermil, setReteIcaPermil] = useState<number>(9.66);
  const [applyReteIva, setApplyReteIva] = useState<boolean>(false);

  const result = settleDianTaxes({
    subtotal,
    ivaRate,
    reteFuenteRate,
    reteIcaPermil,
    applyReteIva,
    thirdPartyType: 'DECLARANTE',
  });

  const handleApplyToVoucher = () => {
    if (!onAddVoucherLineFromTax) return;
    const generatedLines = [
      { id: Date.now() + '-1', accountCode: '13050501', accountName: 'Clientes Nacionales', thirdPartyNit: '900123456-1', thirdPartyName: 'Cliente Ejemplo', concept: 'Liquidación Factura', debit: result.totalPayable, credit: 0 },
      { id: Date.now() + '-2', accountCode: '135515', accountName: 'Retención Fuente 2.5%', thirdPartyNit: '900123456-1', thirdPartyName: 'Cliente Ejemplo', concept: 'Retefuente practicada', debit: result.reteFuenteAmount, credit: 0 },
      { id: Date.now() + '-3', accountCode: '135518', accountName: 'ReteICA 9.66/1000', thirdPartyNit: '900123456-1', thirdPartyName: 'Cliente Ejemplo', concept: 'ReteICA practicado', debit: result.reteIcaAmount, credit: 0 },
      { id: Date.now() + '-4', accountCode: '413505', accountName: 'Ventas de Servicios', thirdPartyNit: '900123456-1', thirdPartyName: 'Cliente Ejemplo', concept: 'Base Gravable', debit: 0, credit: result.subtotal },
      { id: Date.now() + '-5', accountCode: '240801', accountName: 'IVA Generado 19%', thirdPartyNit: '900123456-1', thirdPartyName: 'Cliente Ejemplo', concept: 'IVA Generado', debit: 0, credit: result.ivaAmount },
    ];
    onAddVoucherLineFromTax(generatedLines);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2 text-emerald-400 font-medium">
          <Calculator className="w-4 h-4" />
          <span>Liquidación de Impuestos DIAN (Estatuto Tributario)</span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div>
          <label className="text-slate-400 block mb-1">Subtotal Base (COP)</label>
          <input
            type="number"
            value={subtotal}
            onChange={(e) => setSubtotal(Math.max(0, Number(e.target.value)))}
            className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-100 font-mono focus:border-emerald-500"
          />
        </div>
        <div>
          <label className="text-slate-400 block mb-1">Tarifa IVA (%)</label>
          <select
            value={ivaRate}
            onChange={(e) => setIvaRate(Number(e.target.value))}
            className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-100 font-mono"
          >
            <option value={19}>19% General</option>
            <option value={5}>5% Reducida</option>
            <option value={0}>0% Exento</option>
          </select>
        </div>
        <div>
          <label className="text-slate-400 block mb-1">ReteFuente (%)</label>
          <select
            value={reteFuenteRate}
            onChange={(e) => setReteFuenteRate(Number(e.target.value))}
            className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-100 font-mono"
          >
            <option value={2.5}>2.5% Compras Generales</option>
            <option value={3.5}>3.5% Compras No Declarantes</option>
            <option value={4.0}>4.0% Servicios</option>
            <option value={11.0}>11.0% Honorarios</option>
            <option value={0}>0.0% Sin Retención</option>
          </select>
        </div>
        <div>
          <label className="text-slate-400 block mb-1">ReteICA (&permil;)</label>
          <select
            value={reteIcaPermil}
            onChange={(e) => setReteIcaPermil(Number(e.target.value))}
            className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-slate-100 font-mono"
          >
            <option value={9.66}>9.66 &permil; Comercial</option>
            <option value={11.04}>11.04 &permil; Servicios</option>
            <option value={4.14}>4.14 &permil; Industrial</option>
            <option value={0}>0.0 &permil;</option>
          </select>
        </div>
      </div>

      <div className="bg-slate-950/80 rounded-lg p-3 border border-slate-800/80 grid grid-cols-2 sm:grid-cols-5 gap-3 font-mono text-xs">
        <div>
          <span className="text-slate-400 block text-[10px]">(+) IVA</span>
          <span className="text-emerald-400 font-semibold">{formatCop(result.ivaAmount)}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">(-) ReteFuente</span>
          <span className="text-rose-400 font-semibold">{formatCop(result.reteFuenteAmount)}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">(-) ReteICA</span>
          <span className="text-amber-400 font-semibold">{formatCop(result.reteIcaAmount)}</span>
        </div>
        <div>
          <span className="text-slate-400 block text-[10px]">Neto a Cobrar/Pagar</span>
          <span className="text-sky-300 font-bold">{formatCop(result.totalPayable)}</span>
        </div>
        <div className="flex items-end">
          <Button size="sm" variant="secondary" onClick={handleApplyToVoucher} className="w-full gap-1">
            <PlusCircle className="w-3.5 h-3.5 text-emerald-400" />
            Generar Asiento
          </Button>
        </div>
      </div>
    </div>
  );
};