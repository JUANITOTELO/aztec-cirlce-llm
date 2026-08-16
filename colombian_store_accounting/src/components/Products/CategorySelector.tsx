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
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">Categoría</label>
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={selectedCategory}
          onChange={(e) => onSelect(e.target.value)}
          className="flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
        >
          <option value="">Selecciona una categoría</option>
          {categories.map((cat) => (
            <option key={cat.id || cat.name} value={cat.name}>
              {cat.name}
            </option>
          ))}
        </select>
        {onQuickAdd && (
          !isAdding ? (
            <button
              type="button"
              onClick={() => setIsAdding(true)}
              className="p-2 border rounded-lg hover:bg-gray-50 text-gray-600"
              title="Nueva categoría rápida"
            >
              <Plus className="w-4 h-4" />
            </button>
          ) : (
            <div className="flex items-center gap-1">
              <input
                type="text"
                value={newCatName}
                onChange={(e) => setNewCatName(e.target.value)}
                placeholder="Nueva cat..."
                className="px-2 py-1.5 border rounded text-sm w-28 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <button
                type="button"
                onClick={handleAdd}
                className="p-1.5 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                <Check className="w-3.5 h-3.5"
              />
              </button>
            </div>
          )
        )}
      </div>
    </div>
  );
};
