import React, { useState } from 'react';
import { Plus, Tags, Filter } from 'lucide-react';
import { Product, UserAccount, RoleItem } from '../../types/store';
import { Category, CategoryMutationPayload } from '../../types/category';
import { ProductPricingRecord, StockAdjustmentPayload } from '../../types/product';
import { ProductListTable } from './ProductListTable';
import { ProductModalForm } from './ProductModalForm';
import { ProductStatsCards } from './ProductStatsCards';
import { CategoryManagerModal } from './CategoryManagerModal';
import { ProductStockAdjustModal } from './ProductStockAdjustModal';
import { ProductPricingHistoryModal } from './ProductPricingHistoryModal';
import { useProductPermissions } from '../../hooks/useProductPermissions';
import { useCategoryPermissions } from '../../hooks/useCategoryPermissions';
import { ProductLedgerOrchestrator } from '../../engine/productLedgerOrchestrator';

interface ProductManagementViewProps {
  products: Product[];
  setProducts: React.Dispatch<React.SetStateAction<Product[]>>;
  categories: Category[];
  onAddCategory: (payload: CategoryMutationPayload) => Promise<Category>;
  onUpdateCategory: (id: string, payload: CategoryMutationPayload) => Promise<Category>;
  onDeleteCategory: (id: string) => Promise<void>;
  onReassignCategory?: (sourceName: string, targetName: string) => void;
  currentUser?: UserAccount | null;
  roles?: RoleItem[];
}

const DEFAULT_ADMIN_USER: UserAccount = {
  id: 'usr-admin',
  name: 'Administrador General',
  email: 'admin@aztec.co',
  roleId: 'role-admin',
  role: 'admin',
};

export const ProductManagementView: React.FC<ProductManagementViewProps> = ({
  products,
  setProducts,
  categories,
  onAddCategory,
  onUpdateCategory,
  onDeleteCategory,
  onReassignCategory,
  currentUser = DEFAULT_ADMIN_USER,
  roles = [],
}) => {
  const [isProductModalOpen, setIsProductModalOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [isCategoryModalOpen, setIsCategoryModalOpen] = useState(false);
  const [isStockModalOpen, setIsStockModalOpen] = useState(false);
  const [adjustingProduct, setAdjustingProduct] = useState<Product | null>(null);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [pricingRecords, setPricingRecords] = useState<ProductPricingRecord[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>('ALL');

  const effectiveUser = currentUser || DEFAULT_ADMIN_USER;
  const permissions = useProductPermissions(effectiveUser, roles);
  const { canCreateProduct } = permissions;
  const { canManageCategories } = useCategoryPermissions(effectiveUser, roles);

  const handleSaveProduct = (formData: any) => {
    if (editingProduct) {
      // Record pricing audit if price or cost changed
      if (editingProduct.price !== formData.price || editingProduct.cost !== formData.cost) {
        const auditRecord = ProductLedgerOrchestrator.createPricingAuditRecord(
          editingProduct,
          formData,
          effectiveUser.name,
          'Edición en panel de productos'
        );
        setPricingRecords((prev) => [auditRecord, ...prev]);
      }
      setProducts((prev) =>
        prev.map((p) =>
          p.id === editingProduct.id
            ? { ...p, ...formData, updatedAt: new Date().toISOString() }
            : p
        )
      );
    } else {
      const newProduct: Product = {
        ...formData,
        id: `prod-${Date.now()}`,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      setProducts((prev) => [...prev, newProduct]);
    }
    setIsProductModalOpen(false);
    setEditingProduct(null);
  };

  const handleDeleteProduct = (productId: string) => {
    if (window.confirm('¿Está seguro de eliminar este producto?')) {
      setProducts((prev) => prev.filter((p) => p.id !== productId));
    }
  };

  const handleConfirmStockAdjustment = (payload: StockAdjustmentPayload) => {
    setProducts((prev) =>
      prev.map((p) => {
        if (p.id !== payload.productId) return p;
        const isAdd = payload.adjustmentType === 'ADD' || payload.type === 'INFLOW';
        const newStock = isAdd ? p.stock + payload.quantity : Math.max(0, p.stock - payload.quantity);
        return { ...p, stock: newStock };
      })
    );
  };

  const filteredProducts = products.filter((p) => {
    if (selectedCategoryFilter !== 'ALL' && (p.category || '').toLowerCase() !== selectedCategoryFilter.toLowerCase()) {
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

  return (
    <div className="space-y-6">
      <ProductStatsCards products={products} categories={categories} />

      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex flex-1 items-center gap-3 w-full">
          <div className="w-full sm:w-72">
            <input
              type="text"
              placeholder="Buscar productos..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-slate-700 bg-slate-800 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 placeholder-slate-400 text-sm"
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
          {canManageCategories && (
            <button
              onClick={() => setIsCategoryModalOpen(true)}
              className="flex items-center gap-2 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm font-medium transition"
            >
              <Tags className="w-4 h-4 text-purple-400" />
              <span>Categorías</span>
            </button>
          )}
          {canCreateProduct && (
            <button
              onClick={() => {
                setEditingProduct(null);
                setIsProductModalOpen(true);
              }}
              className="flex items-center gap-2 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium shadow-md shadow-emerald-900/30 transition"
            >
              <Plus className="w-4 h-4" />
              <span>Nuevo Producto</span>
            </button>
          )}
        </div>
      </div>

      <ProductListTable
        products={filteredProducts}
        categories={categories}
        searchQuery=""
        permissions={permissions}
        onEdit={(prod) => {
          setEditingProduct(prod);
          setIsProductModalOpen(true);
        }}
        onDelete={handleDeleteProduct}
        onAdjustStock={(prod) => {
          setAdjustingProduct(prod);
          setIsStockModalOpen(true);
        }}
        onViewHistory={() => {
          setIsHistoryModalOpen(true);
        }}
      />

      {isProductModalOpen && (
        <ProductModalForm
          isOpen={isProductModalOpen}
          initialData={editingProduct}
          categories={categories}
          onClose={() => {
            setIsProductModalOpen(false);
            setEditingProduct(null);
          }}
          onSave={handleSaveProduct}
        />
      )}

      {isCategoryModalOpen && (
        <CategoryManagerModal
          isOpen={isCategoryModalOpen}
          categories={categories}
          products={products}
          onClose={() => setIsCategoryModalOpen(false)}
          onAddCategory={onAddCategory}
          onUpdateCategory={onUpdateCategory}
          onDeleteCategory={onDeleteCategory}
        />
      )}

      {isStockModalOpen && adjustingProduct && (
        <ProductStockAdjustModal
          isOpen={isStockModalOpen}
          product={adjustingProduct}
          currentUserName={effectiveUser.name}
          onClose={() => {
            setIsStockModalOpen(false);
            setAdjustingProduct(null);
          }}
          onConfirm={handleConfirmStockAdjustment}
        />
      )}

      {isHistoryModalOpen && (
        <ProductPricingHistoryModal
          isOpen={isHistoryModalOpen}
          records={pricingRecords}
          onClose={() => setIsHistoryModalOpen(false)}
        />
      )}
    </div>
  );
};
