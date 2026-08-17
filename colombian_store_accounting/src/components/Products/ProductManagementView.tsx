import React, { useState, useMemo } from 'react';
import { Product, UserAccount, RoleItem } from '../../types/store';
import { Category } from '../../types/category';
import { ProductVariant } from '../../types/productVariant';
import { ProductImage } from '../../types/productMedia';
import { ProductStatsCards } from './ProductStatsCards';
import { ProductListTable } from './ProductListTable';
import { CategoryManagerModal } from './CategoryManagerModal';
import { ProductPricingHistoryModal } from './ProductPricingHistoryModal';
import { ProductStockAdjustModal } from './ProductStockAdjustModal';
import { ProductUnifiedModal } from './ProductUnifiedModal';
import { useVariantSync } from '../../hooks/useVariantSync';
import { useImageSync } from '../../hooks/useImageSync';
import { Plus, Tags, Search } from 'lucide-react';

export interface ProductManagementViewProps {
  products: Product[];
  setProducts: React.Dispatch<React.SetStateAction<Product[]>>;
  variants: ProductVariant[];
  setVariants: React.Dispatch<React.SetStateAction<ProductVariant[]>>;
  images: ProductImage[];
  setImages: React.Dispatch<React.SetStateAction<ProductImage[]>>;
  categories: Category[];
  onAddCategory: (category: any) => void;
  onUpdateCategory: (id: string, category: any) => void;
  onDeleteCategory: (id: string) => void;
  onReassignCategory?: (sourceName: string, targetName: string) => void;
  currentUser?: UserAccount;
  roles?: RoleItem[];
}

export const ProductManagementView: React.FC<ProductManagementViewProps> = ({
  products,
  setProducts,
  variants,
  setVariants,
  images,
  setImages,
  categories,
  onAddCategory,
  onUpdateCategory,
  onDeleteCategory,
  onReassignCategory,
  currentUser,
}) => {
  const [isUnifiedModalOpen, setIsUnifiedModalOpen] = useState(false);
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [isStockModalOpen, setIsStockModalOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>('ALL');

  useVariantSync(variants, setVariants);
  useImageSync(images, setImages);

  const handleSaveProduct = (savedProd: Product) => {
    setProducts((prev) => {
      const exists = prev.some((p) => p.id === savedProd.id);
      if (exists) {
        return prev.map((p) => (p.id === savedProd.id ? savedProd : p));
      }
      return [savedProd, ...prev];
    });
    setIsUnifiedModalOpen(false);
  };

  const handleDeleteProduct = (productId: string) => {
    setProducts((prev) => prev.filter((p) => p.id !== productId));
  };

  const filteredProducts = useMemo(() => {
    return products.filter((p) => {
      if (selectedCategoryFilter !== 'ALL' && p.category !== selectedCategoryFilter) {
        return false;
      }
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        (p.name || '').toLowerCase().includes(q) ||
        (p.sku || '').toLowerCase().includes(q) ||
        (p.category || '').toLowerCase().includes(q)
      );
    });
  }, [products, selectedCategoryFilter, searchQuery]);

  return (
    <div className="space-y-6">
      <ProductStatsCards products={products} categories={categories} />

      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex flex-1 items-center gap-3 w-full">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar productos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 border border-slate-700 bg-slate-800 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 placeholder-slate-400 text-sm"
            />
          </div>

          <div className="relative">
            <select
              value={selectedCategoryFilter}
              onChange={(e) => setSelectedCategoryFilter(e.target.value)}
              className="px-3 py-2 border border-slate-700 bg-slate-800 text-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="ALL">Todas las Categorías ({categories.length})</option>
              {categories.map((c) => (
                <option key={c.id} value={c.name}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsCategoryModalOpen(true)}
            className="flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition"
          >
            <Tags className="w-4 h-4 text-purple-400" />
            <span>Categorías</span>
          </button>
          <button
            onClick={() => {
              setSelectedProduct(null);
              setIsUnifiedModalOpen(true);
            }}
            className="flex items-center gap-2 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium shadow-md shadow-emerald-900/30 transition"
          >
            <Plus className="w-4 h-4" />
            <span>Nuevo Producto</span>
          </button>
        </div>
      </div>

      <ProductListTable
        products={filteredProducts}
        images={images}
        categories={categories}
        onEdit={(prod) => {
          setSelectedProduct(prod);
          setIsUnifiedModalOpen(true);
        }}
        onDelete={handleDeleteProduct}
        onAdjustStock={(prod) => {
          setSelectedProduct(prod);
          setIsStockModalOpen(true);
        }}
        onViewHistory={(prod) => {
          setSelectedProduct(prod);
          setIsHistoryModalOpen(true);
        }}
      />

      {isUnifiedModalOpen && (
        <ProductUnifiedModal
          isOpen={isUnifiedModalOpen}
          product={selectedProduct}
          categories={categories}
          variants={variants}
          images={images}
          onSave={handleSaveProduct}
          onClose={() => {
            setIsUnifiedModalOpen(false);
            setSelectedProduct(null);
          }}
          onUpdateVariants={setVariants}
          onUpdateImages={(updatedImgs) => {
            setImages((prev) => {
              const map = new Map(prev.map((img) => [img.id, img]));
              updatedImgs.forEach((img) => map.set(img.id, img));
              return Array.from(map.values());
            });
          }}
        />
      )}

      {isCategoryModalOpen && (
        <CategoryManagerModal
          isOpen={isCategoryModalOpen}
          categories={categories}
          products={products}
          onClose={() => setIsCategoryModalOpen(false)}
          onAddCategory={async (p) => { onAddCategory(p as any); return p as any; }}
          onUpdateCategory={async (id, p) => { onUpdateCategory(id, p as any); return p as any; }}
          onDeleteCategory={async (id) => { onDeleteCategory(id); }}
        />
      )}

      {isStockModalOpen && selectedProduct && (
        <ProductStockAdjustModal
          isOpen={isStockModalOpen}
          product={selectedProduct}
          currentUserName={currentUser?.name || 'Administrador'}
          onClose={() => {
            setIsStockModalOpen(false);
            setSelectedProduct(null);
          }}
          onConfirm={(payload) => {
            handleSaveProduct({
              ...selectedProduct,
              stock: payload.type === 'ADD' ? selectedProduct.stock + payload.quantity : Math.max(0, selectedProduct.stock - payload.quantity),
            });
            setIsStockModalOpen(false);
          }}
        />
      )}

      {isHistoryModalOpen && selectedProduct && (
        <ProductPricingHistoryModal
          isOpen={isHistoryModalOpen}
          records={[]}
          onClose={() => {
            setIsHistoryModalOpen(false);
            setSelectedProduct(null);
          }}
        />
      )}
    </div>
  );
};

export default ProductManagementView;
