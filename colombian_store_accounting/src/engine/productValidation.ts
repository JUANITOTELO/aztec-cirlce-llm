import { ProductFormData, ProductValidationError, ProductCategory } from '../types/product';
import { Product } from '../types/store';

export const VALID_CATEGORIES: ProductCategory[] = [
  'Abarrotes', 'Bebidas', 'Lácteos', 'Aseo', 'Snacks', 'Panadería', 'Otros'
];

export const VALID_IVA_RATES = [0.00, 0.05, 0.19];

export function validateBarcode(barcode: string): boolean {
  if (!barcode) return true; // Barcode can be optional or generated
  const clean = barcode.trim();
  return /^[0-9A-Za-z-]{3,50}$/.test(clean);
}

export function validateSKU(sku: string, existingProducts: Product[], currentId?: string): boolean {
  if (!sku || sku.trim().length < 2) return false;
  const normalized = sku.trim().toUpperCase();
  return !existingProducts.some(p => p.sku.toUpperCase() === normalized && p.id !== currentId);
}

export function validateProductForm(
  data: ProductFormData,
  existingProducts: Product[],
  currentId?: string
): ProductValidationError[] {
  const errors: ProductValidationError[] = [];

  if (!data.sku || data.sku.trim().length < 2) {
    errors.push({ field: 'sku', message: 'El SKU debe tener al menos 2 caracteres.' });
  } else if (!validateSKU(data.sku, existingProducts, currentId)) {
    errors.push({ field: 'sku', message: 'El SKU ya se encuentra registrado en otro producto.' });
  }

  if (!data.name || data.name.trim().length < 3) {
    errors.push({ field: 'name', message: 'El nombre debe tener al menos 3 caracteres.' });
  }

  if (data.price < 0 || isNaN(data.price)) {
    errors.push({ field: 'price', message: 'El precio de venta no puede ser negativo.' });
  }

  if (data.cost < 0 || isNaN(data.cost)) {
    errors.push({ field: 'cost', message: 'El costo unitario no puede ser negativo.' });
  }

  if (data.stock < 0 || isNaN(data.stock)) {
    errors.push({ field: 'stock', message: 'El stock no puede ser negativo.' });
  }

  if (data.minStock < 0 || isNaN(data.minStock)) {
    errors.push({ field: 'minStock', message: 'El stock mínimo no puede ser negativo.' });
  }

  if (!VALID_IVA_RATES.includes(Number(data.ivaRate))) {
    errors.push({ field: 'ivaRate', message: 'Tarifa IVA inválida. Permitidas: 0%, 5%, 19%.' });
  }

  if (data.barcode && !validateBarcode(data.barcode)) {
    errors.push({ field: 'barcode', message: 'El código de barras contiene caracteres inválidos.' });
  }

  return errors;
}
