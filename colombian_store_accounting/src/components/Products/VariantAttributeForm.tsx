import React from 'react';
import { VariantAttributes } from '../../types/productVariant';

interface Props {
  attributes: VariantAttributes;
  onChange: (attrs: VariantAttributes) => void;
  disabled?: boolean;
}

export const VariantAttributeForm: React.FC<Props> = ({ attributes, onChange, disabled }) => {
  const [newKey, setNewKey] = React.useState('');
  const [newVal, setNewVal] = React.useState('');

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newVal.trim()) return;
    onChange({ ...attributes, [newKey.trim()]: newVal.trim() });
    setNewKey('');
    setNewVal('');
  };

  const handleRemove = (key: string) => {
    const updated = { ...attributes };
    delete updated[key];
    onChange(updated);
  };

  return (
    <div className="space-y-3 bg-slate-950/40 p-3 rounded-lg border border-slate-700/60">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold uppercase tracking-wider text-cyan-400">Atributos (Talla, Color, Presentación)</label>
      </div>
      <div className="flex flex-wrap gap-2 min-h-[32px]">
        {Object.entries(attributes).map(([k, v]) => (
          <span key={k} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-800 border border-slate-600 text-xs text-slate-200">
            <strong className="text-cyan-300 font-medium">{k}:</strong> {v}
            {!disabled && (
              <button type="button" onClick={() => handleRemove(k)} className="ml-1 text-slate-400 hover:text-red-400 font-bold transition-colors">&times;</button>
            )}
          </span>
        ))}
        {Object.keys(attributes).length === 0 && (
          <p className="text-xs text-slate-400 italic">Sin atributos específicos asignados.</p>
        )}
      </div>
      {!disabled && (
        <div className="flex gap-2 pt-1">
          <input
            type="text"
            placeholder="Ej: Color"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
            className="w-1/3 px-2 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-slate-100 placeholder-slate-400 focus:border-cyan-500 focus:outline-none"
          />
          <input
            type="text"
            placeholder="Ej: Azul"
            value={newVal}
            onChange={(e) => setNewVal(e.target.value)}
            className="w-1/2 px-2 py-1 text-xs bg-slate-900 border border-slate-700 rounded text-slate-100 placeholder-slate-400 focus:border-cyan-500 focus:outline-none"
          />
          <button
            type="button"
            onClick={handleAdd}
            disabled={!newKey.trim() || !newVal.trim()}
            className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-medium rounded transition-colors"
          >
            + Agregar
          </button>
        </div>
      )}
    </div>
  );
};
