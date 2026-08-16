import React, { useState } from 'react';
import { X, Plus, Edit2, Trash2, Tag, AlertCircle } from 'lucide-react';
import { Category, CategoryMutationPayload } from '../../types/category';
import { Product } from '../../types/store';

interface CategoryManagerModalProps {
  isOpen: boolean;
  onClose: () => void;
  categories: Category[];
  products: Product[];
  onAddCategory?: (payload: CategoryMutationPayload) => Promise<Category>;
  onUpdateCategory?: (id: string, payload: CategoryMutationPayload) => Promise<Category>;
  onDeleteCategory?: (id: string) => Promise<void>;
  onAdd?: (payload: CategoryMutationPayload) => Promise<Category>;
  onUpdate?: (id: string, payload: CategoryMutationPayload) => Promise<Category>;
  onDelete?: (id: string) => Promise<void>;
}

export const CategoryManagerModal: React.FC<CategoryManagerModalProps> = ({
  isOpen,
  onClose,
  categories,
  onAddCategory,
  onUpdateCategory,
  onDeleteCategory,
  onAdd,
  onUpdate,
  onDelete,
}) => {
  const [newCatName, setNewCatName] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = newCatName.trim();
    if (!name) return;
    try {
      const fn = onAddCategory || onAdd;
      if (fn) await fn({ name });
      setNewCatName('');
      setError(null);
    } catch (err: any) {
      setError(err?.message || 'Error al agregar categoría');
    }
  };

  const handleUpdate = async (id: string) => {
    const name = editName.trim();
    if (!name) return;
    try {
      const fn = onUpdateCategory || onUpdate;
      if (fn) await fn(id, { name });
      setEditingId(null);
      setError(null);
    } catch (err: any) {
      setError(err?.message || 'Error al actualizar categoría');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const fn = onDeleteCategory || onDelete;
      if (fn) await fn(id);
      setError(null);
    } catch (err: any) {
      setError(err?.message || 'Error al eliminar categoría');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden border border-slate-700 animate-in fade-in duration-200">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/80 bg-slate-850">
          <div className="flex items-center gap-2">
            <Tag className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-bold text-white">Gestión de Categorías</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          {error && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl flex items-center gap-2 text-sm">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleAdd} className="flex gap-2">
            <input
              type="text"
              value={newCatName}
              onChange={(e) => setNewCatName(e.target.value)}
              placeholder="Nueva categoría..."
              className="flex-1 px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 text-white placeholder-slate-500 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            />
            <button
              type="submit"
              className="flex items-center gap-1.5 px-4 py-2.5 bg-emerald-600 text-white rounded-xl hover:bg-emerald-500 font-semibold text-sm shadow-lg shadow-emerald-900/30 transition-colors"
            >
              <Plus className="w-4 h-4" /> Agregar
            </button>
          </form>

          <div className="max-h-64 overflow-y-auto divide-y divide-slate-700/60 rounded-xl border border-slate-700/50 bg-slate-900/40 p-2">
            {categories.map((cat) => (
              <div key={cat.id} className="py-2.5 px-2 flex items-center justify-between">
                {editingId === cat.id ? (
                  <div className="flex items-center gap-2 flex-1 mr-2">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 text-white rounded-lg text-sm flex-1 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    />
                    <button
                      onClick={() => handleUpdate(cat.id)}
                      className="text-xs bg-emerald-600 hover:bg-emerald-500 text-white px-2.5 py-1.5 rounded-lg font-semibold transition-colors"
                    >
                      Guardar
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-2.5 py-1.5 rounded-lg font-medium transition-colors"
                    >
                      Cancelar
                    </button>
                  </div>
                ) : (
                  <>
                    <span className="font-medium text-slate-200 text-sm">{cat.name}</span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => {
                          setEditingId(cat.id);
                          setEditName(cat.name);
                        }}
                        className="p-1.5 text-slate-400 hover:text-emerald-400 hover:bg-slate-700/50 rounded-lg transition-colors"
                        title="Editar nombre"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(cat.id)}
                        className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-700/50 rounded-lg transition-colors"
                        title="Eliminar categoría"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
