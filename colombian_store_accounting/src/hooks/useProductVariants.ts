import { useState, useCallback } from 'react';
import { ProductVariant, ProductVariantFormData } from '../types/productVariant';
import { sanitizeVariantName, sanitizeVariantSku, sanitizeAttributes } from '../engine/variantSanitization';
import { createVariantAuditEntry, logVariantMutation } from '../engine/variantAuditLogger';
import { db, addTransactionToQueue } from '../db/dexie';

export function useProductVariants(initialVariants: ProductVariant[], userId: string = 'sys') {
  const [variants, setVariants] = useState<ProductVariant[]>(initialVariants);
  const [error, setError] = useState<string | null>(null);

  const addVariant = useCallback(async (productId: string, form: ProductVariantFormData) => {
    setError(null);
    const cleanSku = sanitizeVariantSku(form.sku);
    if (variants.some((v) => v.productId === productId && v.sku === cleanSku)) {
      setError(`El SKU ${cleanSku} ya existe para este producto.`);
      return null;
    }
    const now = new Date().toISOString();
    const newVariant: ProductVariant = {
      id: `var-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      productId,
      sku: cleanSku,
      name: sanitizeVariantName(form.name),
      barcode: form.barcode?.trim() || '',
      price: Number(form.price) || 0,
      cost: Number(form.cost) || 0,
      stock: Number(form.stock) || 0,
      minStock: Number(form.minStock) || 0,
      attributes: sanitizeAttributes(form.attributes || {}),
      isDefault: Boolean(form.isDefault),
      isActive: Boolean(form.isActive),
      createdAt: now,
      updatedAt: now,
    };

    setVariants((prev) => [...prev, newVariant]);
    await db.productVariants.put(newVariant);
    const audit = createVariantAuditEntry(newVariant.id, productId, 'CREATED', userId, {}, newVariant);
    await logVariantMutation(audit);
    await addTransactionToQueue('VARIANT_MUTATION', { action: 'CREATED', variant: newVariant });
    return newVariant;
  }, [variants, userId]);

  const updateVariant = useCallback(async (id: string, form: Partial<ProductVariantFormData>) => {
    setError(null);
    const old = variants.find((v) => v.id === id);
    if (!old) return;
    const updated: ProductVariant = {
      ...old,
      ...form,
      sku: form.sku ? sanitizeVariantSku(form.sku) : old.sku,
      name: form.name ? sanitizeVariantName(form.name) : old.name,
      attributes: form.attributes ? sanitizeAttributes(form.attributes) : old.attributes,
      updatedAt: new Date().toISOString(),
    };
    setVariants((prev) => prev.map((v) => (v.id === id ? updated : v)));
    await db.productVariants.put(updated);
    const audit = createVariantAuditEntry(id, old.productId, 'UPDATED', userId, old, updated);
    await logVariantMutation(audit);
    await addTransactionToQueue('VARIANT_MUTATION', { action: 'UPDATED', variant: updated });
  }, [variants, userId]);

  const deleteVariant = useCallback(async (id: string) => {
    const target = variants.find((v) => v.id === id);
    if (!target) return;
    setVariants((prev) => prev.filter((v) => v.id !== id));
    await db.productVariants.delete(id);
    const audit = createVariantAuditEntry(id, target.productId, 'DELETED', userId, target, {});
    await logVariantMutation(audit);
    await addTransactionToQueue('VARIANT_MUTATION', { action: 'DELETED', variantId: id, productId: target.productId });
  }, [variants, userId]);

  return { variants, setVariants, addVariant, updateVariant, deleteVariant, error };
}