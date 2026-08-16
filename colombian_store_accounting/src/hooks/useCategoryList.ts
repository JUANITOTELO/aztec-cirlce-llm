import { useState, useCallback, useRef } from 'react';
import { Category, CategoryMutationPayload } from '../types/category';
import { INITIAL_CATEGORIES } from '../constants/mockCategories';
import { sanitizeCategoryText, validateCategoryPayload } from '../engine/categoryConstraints';
import { db } from '../db/dexie';

const MAX_MUTATIONS_PER_MINUTE = 15;

export function useCategoryList(initialCategories: Category[] = INITIAL_CATEGORIES) {
  const [categories, setCategories] = useState<Category[]>(initialCategories);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const mutationTimestamps = useRef<number[]>([]);

  const checkRateLimit = (): boolean => {
    const now = Date.now();
    mutationTimestamps.current = mutationTimestamps.current.filter((t) => now - t < 60000);
    if (mutationTimestamps.current.length >= MAX_MUTATIONS_PER_MINUTE) {
      setError('Límite de operaciones alcanzado. Por favor espera un minuto.');
      return false;
    }
    mutationTimestamps.current.push(now);
    return true;
  };

  const addCategory = useCallback(async (payload: CategoryMutationPayload, userId: string = 'system'): Promise<Category> => {
    if (!checkRateLimit()) throw new Error('Rate limit exceeded');
    const validation = validateCategoryPayload(payload);
    if (!validation.valid) throw new Error(validation.errors.join(', '));

    const safeName = sanitizeCategoryText(payload.name);
    const exists = categories.some((c) => !c.isDeleted && c.name.toLowerCase() === safeName.toLowerCase());
    if (exists) throw new Error(`Ya existe una categoría con el nombre '${safeName}'.`);

    const newCat: Category = {
      id: `cat-${Date.now()}`,
      name: safeName,
      description: payload.description ? sanitizeCategoryText(payload.description) : '',
      color: payload.color || '#2563EB',
      ledgerAccountCode: payload.ledgerAccountCode || '413595',
      ledgerAccountName: payload.ledgerAccountName || 'Comercio al por menor - General',
      isSystem: false,
      isDeleted: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    setIsLoading(true);
    setError(null);
    try {
      await db.categories.add(newCat);
      await db.categoryAuditLogs.add({
        categoryId: newCat.id,
        action: 'CREATE',
        userId,
        timestamp: new Date().toISOString(),
        details: `Categoría creada: ${newCat.name}`,
      });
      setCategories((prev) => [...prev, newCat]);
      return newCat;
    } catch (err: any) {
      setCategories((prev) => [...prev, newCat]);
      return newCat;
    } finally {
      setIsLoading(false);
    }
  }, [categories]);

  const updateCategory = useCallback(async (id: string, payload: CategoryMutationPayload, userId: string = 'system'): Promise<Category> => {
    if (!checkRateLimit()) throw new Error('Rate limit exceeded');
    const validation = validateCategoryPayload(payload);
    if (!validation.valid) throw new Error(validation.errors.join(', '));

    const safeName = sanitizeCategoryText(payload.name);
    const current = categories.find((c) => c.id === id);
    if (!current) throw new Error('Categoría no encontrada');

    const updated: Category = {
      ...current,
      name: safeName,
      description: payload.description !== undefined ? sanitizeCategoryText(payload.description) : current.description,
      color: payload.color || current.color,
      ledgerAccountCode: payload.ledgerAccountCode || current.ledgerAccountCode,
      ledgerAccountName: payload.ledgerAccountName || current.ledgerAccountName,
      updatedAt: new Date().toISOString(),
    };

    setIsLoading(true);
    try {
      await db.categories.put(updated);
      await db.categoryAuditLogs.add({
        categoryId: id,
        action: 'UPDATE',
        userId,
        timestamp: new Date().toISOString(),
        details: `Categoría actualizada: ${updated.name}`,
      });
      setCategories((prev) => prev.map((c) => (c.id === id ? updated : c)));
      return updated;
    } catch (err) {
      setCategories((prev) => prev.map((c) => (c.id === id ? updated : c)));
      return updated;
    } finally {
      setIsLoading(false);
    }
  }, [categories]);

  const deleteCategory = useCallback(async (id: string, userId: string = 'system'): Promise<void> => {
    if (!checkRateLimit()) throw new Error('Rate limit exceeded');
    const cat = categories.find((c) => c.id === id);
    if (!cat) throw new Error('Categoría no encontrada');
    if (cat.isSystem) throw new Error('Las categorías del sistema no pueden ser eliminadas.');

    setIsLoading(true);
    try {
      await db.categories.update(id, { isDeleted: true, updatedAt: new Date().toISOString() });
      await db.categoryAuditLogs.add({
        categoryId: id,
        action: 'DELETE',
        userId,
        timestamp: new Date().toISOString(),
        details: `Categoría desactivada: ${cat.name}`,
      });
      setCategories((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      setCategories((prev) => prev.filter((c) => c.id !== id));
    } finally {
      setIsLoading(false);
    }
  }, [categories]);

  return { categories, setCategories, isLoading, error, setError, addCategory, updateCategory, deleteCategory };
}