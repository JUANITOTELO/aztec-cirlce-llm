import React, { useState } from 'react';
import { Plus, Check } from 'lucide-react';
import { Category } from '../../types/category';

interface CategorySelectorProps {
  categories: Category[];
  selectedCategory: string;
  onSelect: (categoryName: string) => void;
  onQuickAdd?: (name: string) => void;
}

export const CategorySelector: React.FC<CategorySelectorProps> = ({
  categories,
  selectedCategory,
  onSelect,
  onQuickAdd,
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [newCatName, setNewCatName] = useState('');

  const handleAdd = () => {
    if (newCatName.trim() && onQuickAdd) {
      onQuickAdd(newCatName.trim());
      onSelect(newCatName.trim());
      setNewCatName('');
      setIsAdding(false);
    }
  };

  return (
    <div>
      <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
        Categoría
      </label>
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={selectedCategory}
          onChange={(e) => onSelect(e.target.value)}
          className="flex-1 px-3.5 py-2.5 bg-slate-900/90 border border-slate-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
        >
          <option value="" className="bg-slate-900 text-slate-400">Selecciona una categoría</option>
          {categories.map((cat) => (
            <option key={cat.id || cat.name} value={cat.name} className="bg-slate-900 text-white">
              {cat.name}
            </option>
          ))}
        </select>
        {onQuickAdd && (
          !isAdding ? (
            <button
              type="button"
              onClick={() => setIsAdding(true)}
              className="p-2.5 bg-slate-700/50 hover:bg-slate-700 text-slate-300 border border-slate-600 rounded-xl transition-colors"
              title="Nueva categoría rápida"
            >
              <Plus className="w-4 h-4" />
            </button>
          ) : (
            <div className="flex items-center gap-1.5">
              <input
                type="text"
                value={newCatName}
                onChange={(e) => setNewCatName(e.target.value)}
                placeholder="Nueva cat..."
                className="px-3 py-2 bg-slate-900 border border-slate-700 text-white rounded-lg text-sm w-32 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
              <button
                type="button"
                onClick={handleAdd}
                className="p-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-500 transition-colors shadow"
              >
                <Check className="w-4 h-4" />
              </button>
            </div>
          )
        )}
      </div>
    </div>
  );
};
