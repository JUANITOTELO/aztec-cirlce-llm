import React, { useState } from 'react';
import { PUC_CATALOG } from '../constants/pucColombia';
import { PucAccount } from '../types/puc';
import { Badge } from '../atoms/Badge';
import { Search, BookOpen } from 'lucide-react';

export const PucExplorer: React.FC = () => {
  const [filter, setFilter] = useState('');

  const filtered = PUC_CATALOG.filter(
    (acc) =>
      acc.code.includes(filter) ||
      acc.name.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2 text-slate-100 font-semibold">
          <BookOpen className="w-4 h-4 text-emerald-400" />
          <span>Catálogo Plan Único de Cuentas (PUC Colombia)</span>
        </div>
        <div className="relative w-64">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Buscar cuenta o código..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-md pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:border-emerald-500 font-mono"
          />
        </div>
      </div>

      <div className="max-h-[380px] overflow-y-auto border border-slate-800 rounded-lg">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-950 sticky top-0 border-b border-slate-800 text-slate-400">
            <tr>
              <th className="py-2 px-3">Código</th>
              <th className="py-2 px-3">Denominación / Cuenta</th>
              <th className="py-2 px-3">Nivel</th>
              <th className="py-2 px-3 text-center">Naturaleza</th>
              <th className="py-2 px-3 text-center">Permite Movimiento</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40">
            {filtered.map((item: PucAccount) => (
              <tr key={item.code} className="hover:bg-slate-800/40">
                <td className="py-2 px-3 font-semibold text-emerald-400">{item.code}</td>
                <td className="py-2 px-3 text-slate-200" style={{ paddingLeft: `${Math.max(12, item.code.length * 7)}px` }}>
                  {item.name}
                </td>
                <td className="py-2 px-3 text-slate-400">{item.level}</td>
                <td className="py-2 px-3 text-center">
                  <Badge variant={item.nature === 'DEBITO' ? 'info' : 'warning'}>{item.nature}</Badge>
                </td>
                <td className="py-2 px-3 text-center">
                  {item.acceptsMovement ? (
                    <span className="text-emerald-400 font-semibold">SÍ (Auxiliar)</span>
                  ) : (
                    <span className="text-slate-500">NO (Mayor)</span>
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