import { useState, useMemo, useCallback } from 'react';
import { Product, LedgerEntry } from '../types/store';
import { ProductFormData, StockAdjustmentPayload, ProductPricingRecord } from '../types/product';
import { ProductLedgerOrchestrator } from '../engine/productLedgerOrchestrator';
import { validateProductForm } from '../engine/productValidation';

export function useProductManagement(
  products: Product[],
  setProducts: React.Dispatch<React.SetStateAction<Product[]>>,
  setLedgerEntries: React.Dispatch<React.SetStateAction<LedgerEntry[]>>,
  currentUserName: string
) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [sortBy, setSortBy] = useState<'name' | 'sku' | 'price' | 'stock'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [pricingHistory, setPricingHistory] = useState<ProductPricingRecord[]>([]);

  const filteredProducts = useMemo(() => {
    return products
      .filter(p => {
        const matchSearch = p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          p.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (p.barcode && p.barcode.includes(searchTerm));
        const matchCat = selectedCategory === 'ALL' || p.category === selectedCategory;
        return matchSearch && matchCat;
      })
      .sort((a, b) => {
        const valA = a[sortBy];
        const valB = b[sortBy];
        if (typeof valA === 'string' && typeof valB === 'string') {
          return sortOrder === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
        }
        return sortOrder === 'asc' ? (Number(valA) - Number(valB)) : (Number(valB) - Number(valA));
      });
  }, [products, searchTerm, selectedCategory, sortBy, sortOrder]);

  const saveProduct = useCallback((formData: ProductFormData, editId?: string) => {
    const errors = validateProductForm(formData, products, editId);
    if (errors.length > 0) return { success: false, errors };

    if (editId) {
      const existing = products.find(p => p.id === editId);
      if (existing && (existing.price !== formData.price || existing.cost !== formData.cost || existing.ivaRate !== formData.ivaRate)) {
        const record = ProductLedgerOrchestrator.createPricingAuditRecord(existing, formData, currentUserName, 'Modificación manual');
        setPricingHistory(prev => [record, ...prev]);
      }
      setProducts(prev => prev.map(p => (p.id === editId ? { ...p, ...formData } : p)));
    } else {
      const newProd: Product = { id: `prod-${Date.now()}`, ...formData };
      setProducts(prev => [newProd, ...prev]);
    }
    return { success: true, errors: [] };
  }, [products, setProducts, currentUserName]);

  const deleteProduct = useCallback((id: string) => {
    setProducts(prev => prev.filter(p => p.id !== id));
  }, [setProducts]);

  const adjustStock = useCallback((payload: StockAdjustmentPayload) => {
    const target = products.find(p => p.id === payload.productId);
    if (!target) return;

    const qty = payload.adjustmentType === 'ADD' ? payload.quantity : -payload.quantity;
    const newStock = Math.max(0, target.stock + qty);

    setProducts(prev => prev.map(p => (p.id === payload.productId ? { ...p, stock: newStock } : p)));
    const newEntries = ProductLedgerOrchestrator.emitStockAdjustment(payload);
    if (newEntries.length > 0) {
      setLedgerEntries(prev => [...newEntries, ...prev]);
    }
  }, [products, setProducts, setLedgerEntries]);

  return {
    searchTerm, setSearchTerm,
    selectedCategory, setSelectedCategory,
    sortBy, setSortBy,
    sortOrder, setSortOrder,
    filteredProducts,
    pricingHistory,
    saveProduct,
    deleteProduct,
    adjustStock
  };
}
