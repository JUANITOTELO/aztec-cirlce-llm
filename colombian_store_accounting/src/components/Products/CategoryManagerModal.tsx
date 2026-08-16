import React, { useState } from 'react';
import { X, Plus, Edit2, Trash2, Tag } from 'lucide-react';
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
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in duration-200">
        <div className="flex items-center justify-between p-4 border-b">
          <div className="flex items-center gap-2">
            <Tag className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-bold text-gray-900">Gestión de Categorías</h2>
          </div>
          <button onClick={onClose} className="p-1 text-gray-400 hover:text-gray-600 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {error && <div className="p-2.5 bg-red-50 text-red-700 rounded text-sm">{error}</div>}

          <form onSubmit={handleAdd} className="flex gap-2">
            <input
              type="text"
              value={newCatName}
              onChange={(e) => setNewCatName(e.target.value)}
              placeholder="Nueva categoría..."
              className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="flex items-center gap-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Plus className="w-4 h-4" /> Agregar
            </button>
          </form>

          <div className="max-h-60 overflow-y-auto divide-y">
            {categories.map((cat) => (
              <div key={cat.id} className="py-2.5 flex items-center justify-between">
                {editingId === cat.id ? (
                  <div className="flex items-center gap-2 flex-1 mr-2">
                    <input
                      type="text"
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="px-2 py-1 border rounded text-sm flex-1"
                    />
                    <button
                      onClick={() => handleUpdate(cat.id)}
                      className="text-xs bg-green-600 text-white px-2 py-1 rounded"
                    >
                      Guardar
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded"
                    >
                      Cancelar
                    </button>
                  </div>
                ) : (
                  <>
                    <span className="font-medium text-gray-800">{cat.name}</span>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => {
                          setEditingId(cat.id);
                          setEditName(cat.name);
                        }}
                        className="p-1 text-gray-500 hover:text-blue-600 rounded"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(cat.id)}
                        className="p-1 text-gray-500 hover:text-red-600 rounded"
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
