import React, { useState } from 'react';
import { PUC_CATALOG } from '../../constants/mockData';
import { PucAccount } from '../../types/store';
import { FolderTree, Search, Hash, FileCode2 } from 'lucide-react';

export const PucExplorer: React.FC = () => {
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState<string>('Todos');

  const types = ['Todos', 'Activo', 'Pasivo', 'Patrimonio', 'Ingresos', 'Gastos', 'Costos'];

  const filtered = PUC_CATALOG.filter((acc) => {
    const matchesType = selectedType === 'Todos' || acc.type === selectedType;
    const matchesSearch = acc.code.includes(search) || acc.name.toLowerCase().includes(search.toLowerCase());
    return matchesType && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Header & Filter Card */}
      <div className="bg-slate-800/90 border border-slate-700 p-5 rounded-xl flex flex-wrap items-center justify-between gap-4 shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-sky-600/20 text-sky-400 flex items-center justify-center border border-sky-500/30">
            <FolderTree className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              Plan Único de Cuentas (PUC Comercial Colombia)
            </h2>
            <p className="text-xs text-slate-400">
              Estructura jerárquica de cuentas codificadas bajo Decreto 2650 y NIIF
            </p>
          </div>
        </div>

        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
          <input
            type="text"
            placeholder="Buscar código (ej: 110505) o nombre..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-white text-xs placeholder-slate-400 focus:outline-none focus:border-sky-500"
          />
        </div>
      </div>

      {/* Class filter tags */}
      <div className="flex flex-wrap gap-2">
        {types.map((t) => (
          <button
            key={t}
            onClick={() => setSelectedType(t)}
            className={`text-xs px-3 py-1.5 rounded-lg font-medium transition ${
              selectedType === t
                ? 'bg-sky-600 text-white shadow-sm'
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* PUC Table */}
      <div className="bg-slate-800/80 border border-slate-700 rounded-xl p-5 shadow-lg">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-700">
              <tr>
                <th className="p-3 w-32">Código PUC</th>
                <th className="p-3">Nombre de la Cuenta</th>
                <th className="p-3 w-28">Naturaleza</th>
                <th className="p-3 w-28 text-center">Nivel Jerárquico</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/60 font-mono">
              {filtered.map((acc) => {
                const isClase = acc.level === 1;
                const isGrupo = acc.level === 2;
                const isCuenta = acc.level === 3;
                const isSubcuenta = acc.level === 4;

                const paddingLeft = isClase ? 'pl-3' : isGrupo ? 'pl-6' : isCuenta ? 'pl-10' : 'pl-14';

                return (
                  <tr
                    key={acc.code}
                    className={`hover:bg-slate-700/30 transition ${
                      isClase ? 'bg-slate-900/60 font-bold text-white' : isGrupo ? 'font-semibold text-slate-200' : ''
                    }`}
                  >
                    <td className={`p-3 font-bold ${isClase ? 'text-sky-300 text-sm' : 'text-sky-400'}`}>
                      {acc.code}
                    </td>
                    <td className={`p-3 font-sans ${paddingLeft} flex items-center gap-1.5`}>
                      {isSubcuenta && <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />}
                      <span className={isClase ? 'text-white text-sm font-bold' : isGrupo ? 'text-slate-200' : 'text-slate-300'}>
                        {acc.name}
                      </span>
                    </td>
                    <td className="p-3 font-sans text-xs">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        acc.type === 'Activo' || acc.type === 'Costos' || acc.type === 'Gastos'
                          ? 'bg-emerald-500/20 text-emerald-300'
                          : 'bg-indigo-500/20 text-indigo-300'
                      }`}>
                        {acc.type}
                      </span>
                    </td>
                    <td className="p-3 text-center font-sans text-xs text-slate-400">
                      {isClase ? 'Clase (1 dígito)' : isGrupo ? 'Grupo (2 dígitos)' : isCuenta ? 'Cuenta (4 dígitos)' : 'Subcuenta (6 dígitos)'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PucExplorer;
