import React from 'react';
import { formatCOP } from '../../utils/formatters';
import { Landmark, FileText, Download, ShieldCheck, Calculator } from 'lucide-react';

export const DianTaxSettlement: React.FC = () => {
  // Simulated monthly fiscal calculations for Colombian Tax Settlement
  const grossSales = 14500000;
  const taxableSales19 = 11200000;
  const exemptSales = 3300000;
  const ivaGenerated19 = Math.round(taxableSales19 * 0.19); // $2.128.000
  const ivaDeductible = 840000; // Compras con IVA
  const netIvaPayable = ivaGenerated19 - ivaDeductible;

  const retefuentePurchases = Math.round(6500000 * 0.025); // 2.5% sobre compras = $162.500
  const reteICA = Math.round(grossSales * 0.00966); // 9.66 por mil = $140.070
  const totalTaxPayable = netIvaPayable + retefuentePurchases + reteICA;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-slate-800/90 border border-slate-700 p-5 rounded-xl flex flex-wrap items-center justify-between gap-4 shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-amber-600/20 text-amber-400 flex items-center justify-center border border-amber-500/30">
            <Landmark className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              Liquidación Tributaria DIAN &amp; Retenciones
            </h2>
            <p className="text-xs text-slate-400">
              Formularios 300 (IVA), 350 (Retenciones en la Fuente) y ReteICA Municipal
            </p>
          </div>
        </div>

        <button className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 shadow">
          <Download className="w-4 h-4" /> Exportar Reporte DIAN XML
        </button>
      </div>

      {/* Main Tax Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Form 300 - IVA */}
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded">
              Formulario 300 DIAN
            </span>
            <span className="text-xs text-slate-400 font-mono">Bimestre 4 - 2026</span>
          </div>
          <h3 className="text-base font-bold text-white">Impuesto sobre las Ventas (IVA)</h3>

          <div className="space-y-2 text-xs divide-y divide-slate-700/60">
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Ingresos Gravados (19%):</span>
              <span className="font-mono text-white">{formatCOP(taxableSales19)}</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Ingresos Exentos (0%):</span>
              <span className="font-mono text-white">{formatCOP(exemptSales)}</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">IVA Generado (19%):</span>
              <span className="font-mono text-emerald-400 font-bold">{formatCOP(ivaGenerated19)}</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">IVA Descontable (Compras):</span>
              <span className="font-mono text-slate-300">-{formatCOP(ivaDeductible)}</span>
            </div>
            <div className="flex justify-between pt-2 text-sm font-bold">
              <span className="text-white">Saldo a Pagar IVA:</span>
              <span className="font-mono text-emerald-400">{formatCOP(netIvaPayable)}</span>
            </div>
          </div>
        </div>

        {/* Form 350 - Retención en la Fuente */}
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded">
              Formulario 350 DIAN
            </span>
            <span className="text-xs text-slate-400 font-mono">Mensual - Agosto</span>
          </div>
          <h3 className="text-base font-bold text-white">Retenciones en la Fuente</h3>

          <div className="space-y-2 text-xs divide-y divide-slate-700/60">
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Base Compras Declarantes:</span>
              <span className="font-mono text-white">{formatCOP(6500000)}</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Tarifa Retefuente Compras:</span>
              <span className="font-mono text-slate-300">2.5%</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Retención Practicada:</span>
              <span className="font-mono text-amber-400 font-bold">{formatCOP(retefuentePurchases)}</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Retención Servicios (3.5%):</span>
              <span className="font-mono text-slate-300">$0</span>
            </div>
            <div className="flex justify-between pt-2 text-sm font-bold">
              <span className="text-white">Total Retefuente a Declarar:</span>
              <span className="font-mono text-amber-400">{formatCOP(retefuentePurchases)}</span>
            </div>
          </div>
        </div>

        {/* ReteICA Municipal */}
        <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30 px-2 py-0.5 rounded">
              Impuesto Territorial
            </span>
            <span className="text-xs text-slate-400 font-mono">Bogotá D.C.</span>
          </div>
          <h3 className="text-base font-bold text-white">Industria y Comercio (ICA)</h3>

          <div className="space-y-2 text-xs divide-y divide-slate-700/60">
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Base Ingresos Brutos:</span>
              <span className="font-mono text-white">{formatCOP(grossSales)}</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Tarifa Actividad Comercial:</span>
              <span className="font-mono text-slate-300">9.66 ‰ (por mil)</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Liquidación ICA:</span>
              <span className="font-mono text-sky-400 font-bold">{formatCOP(reteICA)}</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Avisos y Tableros (15%):</span>
              <span className="font-mono text-slate-300">$0</span>
            </div>
            <div className="flex justify-between pt-2 text-sm font-bold">
              <span className="text-white">Total ICA a Pagar:</span>
              <span className="font-mono text-sky-400">{formatCOP(reteICA)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Fiscal Summary Bar */}
      <div className="bg-slate-900 border border-emerald-500/30 p-4 rounded-xl flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <ShieldCheck className="w-6 h-6 text-emerald-400" />
          <div>
            <span className="text-xs text-slate-400 block font-medium">Consolidado Total Obligaciones Tributarias</span>
            <span className="text-lg font-bold text-white">Total Impuestos del Período a Pagar</span>
          </div>
        </div>
        <div className="font-mono text-2xl font-bold text-emerald-400">
          {formatCOP(totalTaxPayable)}
        </div>
      </div>
    </div>
  );
};

export default DianTaxSettlement;
