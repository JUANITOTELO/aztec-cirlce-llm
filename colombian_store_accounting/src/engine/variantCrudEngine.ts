import { ProductVariant, ProductVariantFormData } from '../types/productVariant';
import { ProductImage } from '../types/productMedia';
import { sanitizeVariantName, sanitizeVariantSku } from './variantSanitization';

export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

export function validateVariantPayload(formData: ProductVariantFormData, existing: ProductVariant[], currentId?: string): { isValid: boolean; errors: Record<string, string> } {
  const errors: Record<string, string> = {};
  if (!formData.name?.trim()) errors.name = 'El nombre de la variante es obligatorio';
  if (!formData.sku?.trim()) errors.sku = 'El SKU de la variante es obligatorio';
  if (formData.price < 0) errors.price = 'El precio no puede ser negativo';
  if (formData.cost < 0) errors.cost = 'El costo no puede ser negativo';
  if (formData.stock < 0) errors.stock = 'El inventario no puede ser negativo';
  
  const normalizedSku = sanitizeVariantSku(formData.sku || '');
  const duplicateSku = existing.find(v => v.id !== currentId && v.sku.toUpperCase() === normalizedSku.toUpperCase());
  if (duplicateSku) errors.sku = `El SKU "${normalizedSku}" ya se encuentra registrado`;

  return { isValid: Object.keys(errors).length === 0, errors };
}

export function buildNewVariant(productId: string, formData: ProductVariantFormData): ProductVariant {
  return {
    id: `var-${generateUUID().substring(0, 8)}`,
    productId,
    sku: sanitizeVariantSku(formData.sku),
    name: sanitizeVariantName(formData.name),
    attributes: formData.attributes || {},
    price: Number(formData.price) || 0,
    cost: Number(formData.cost) || 0,
    stock: Number(formData.stock) || 0,
    minStock: Number(formData.minStock) || 0,
    barcode: formData.barcode?.trim() || undefined,
    isActive: formData.isActive !== false,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

export function buildNewImage(productId: string, url: string, fileName: string, size: number, mimeType: string, variantId?: string, isPrimary = false, order = 0): ProductImage {
  return {
    id: `img-${generateUUID().substring(0, 8)}`,
    productId,
    variantId: variantId || undefined,
    url,
    fileName,
    fileSize: size,
    mimeType,
    isPrimary,
    order,
    createdAt: new Date().toISOString(),
  };
}
