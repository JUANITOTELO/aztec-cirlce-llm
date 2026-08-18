import { Product } from '../types/store';
import { Category, CategoryMutationPayload, CategoryConstraintReport } from '../types/category';

const HEX_COLOR_REGEX = /^#([0-9A-F]{3}){1,2}$/i;
const PUC_CODE_REGEX = /^[0-9]{4,6}$/;

export function sanitizeCategoryText(raw: string): string {
  if (!raw) return '';
  return raw
    .replace(/[<>"'/`]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 50);
}

export function validateCategoryPayload(payload: CategoryMutationPayload): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  const sanitizedName = sanitizeCategoryText(payload.name || '');

  if (!sanitizedName || sanitizedName.length < 2) {
    errors.push('El nombre de la categoría debe tener al menos 2 caracteres.');
  }
  if (sanitizedName.length > 50) {
    errors.push('El nombre de la categoría no puede superar 50 caracteres.');
  }
  if (payload.color && !HEX_COLOR_REGEX.test(payload.color)) {
    errors.push('El color debe ser un formato HEX válido (ej: #2563EB).');
  }
  if (payload.ledgerAccountCode && !PUC_CODE_REGEX.test(payload.ledgerAccountCode)) {
    errors.push('El código PUC debe ser numérico de 4 a 6 dígitos (ej: 413505).');
  }
  return {
    valid: errors.length === 0,
    errors,
  };
}

export function checkOrphanProducts(products: Product[], categories: Category[]): CategoryConstraintReport {
  const activeCategoryNames = new Set(categories.filter((c) => !c.isDeleted).map((c) => c.name.toLowerCase()));
  const orphanProductIds: string[] = [];
  const affectedCategoriesSet = new Set<string>();

  products.forEach((product) => {
    const catName = (product.category || '').toLowerCase();
    if (!catName || !activeCategoryNames.has(catName)) {
      orphanProductIds.push(product.id);
      if (product.category) affectedCategoriesSet.add(product.category);
    }
  });

  return {
    hasOrphans: orphanProductIds.length > 0,
    orphanProductCount: orphanProductIds.length,
    orphanProductIds,
    affectedCategories: Array.from(affectedCategoriesSet),
    reassignmentMap: {},
    validationErrors: orphanProductIds.length > 0
      ? [`Existen ${orphanProductIds.length} productos con categorías huérfanas o no registradas.`]
      : [],
  };
}

export function reassignProductsToCategory(
  products: Product[],
  sourceCategoryName: string,
  targetCategoryName: string
): Product[] {
  const target = sanitizeCategoryText(targetCategoryName);
  const source = (sourceCategoryName || '').toLowerCase().trim();
  return products.map((prod) => {
    if ((prod.category || '').toLowerCase().trim() === source) {
      return { ...prod, category: target };
    }
    return prod;
  });
}

export function resolveLedgerAccount(
  categoryName: string,
  categories: Category[]
): { code: string; name: string } {
  const norm = (categoryName || '').toLowerCase().trim();
  const matched = categories.find((c) => !c.isDeleted && c.name.toLowerCase().trim() === norm);
  if (matched && matched.ledgerAccountCode) {
    return {
      code: matched.ledgerAccountCode,
      name: matched.ledgerAccountName || 'Ingresos Operacionales',
    };
  }
  return {
    code: '413595',
    name: 'Comercio al por menor - Otros productos',
  };
}
