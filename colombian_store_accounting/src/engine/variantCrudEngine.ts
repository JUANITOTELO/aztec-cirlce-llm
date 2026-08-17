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

export function validateVariantPayload(
  formData: ProductVariantFormData,
  existing: ProductVariant[] | string[] = [],
  existingBarcodes: string[] = [],
  currentId?: string
): { isValid: boolean; errors: Record<string, string> } {
  const errors: Record<string, string> = {};
  if (!formData.name?.trim()) errors.name = 'El nombre de la variante es obligatorio';
  if (!formData.sku?.trim()) errors.sku = 'El SKU de la variante es obligatorio';
  if (formData.price !== undefined && formData.price < 0) errors.price = 'El precio no puede ser negativo';
  if (formData.cost !== undefined && formData.cost < 0) errors.cost = 'El costo no puede ser negativo';
  if (formData.stock !== undefined && formData.stock < 0) errors.stock = 'El inventario no puede ser negativo';
  
  const barcode = (formData.barcode || '').trim();
  if (barcode) {
    if (!/^[0-9]{8,14}$/.test(barcode)) {
      errors.barcode = 'Código de barras debe ser numérico entre 8 y 14 dígitos.';
    } else if (existingBarcodes && existingBarcodes.includes(barcode)) {
      errors.barcode = `El código de barras "${barcode}" ya está registrado.`;
    }
  }

  const normalizedSku = sanitizeVariantSku(formData.sku || '');
  if (Array.isArray(existing)) {
    const isObjectArray = existing.length > 0 && typeof existing[0] === 'object';
    if (isObjectArray) {
      const duplicate = (existing as ProductVariant[]).find(
        (v) => v.id !== currentId && v.sku.toUpperCase() === normalizedSku.toUpperCase()
      );
      if (duplicate) errors.sku = `El SKU "${normalizedSku}" ya se encuentra registrado`;
    } else {
      const duplicate = (existing as string[]).find(
        (s) => s.toUpperCase() === normalizedSku.toUpperCase()
      );
      if (duplicate) errors.sku = `El SKU "${normalizedSku}" ya está en uso por otra variante.`;
    }
  }

  return { isValid: Object.keys(errors).length === 0, errors };
}

export function buildNewVariant(productId: string, formData: ProductVariantFormData): ProductVariant {
  return {
    id: `var-${generateUUID().substring(0, 8)}`,
    productId,
    sku: sanitizeVariantSku(formData.sku || ''),
    name: sanitizeVariantName(formData.name || ''),
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

export function buildNewImage(
  productId: string,
  urlOrVariantId: string,
  fileNameOrUrl: string,
  sizeOrIsPrimary: number | boolean = false,
  mimeTypeOrOrder: string | number = 0,
  variantIdOrId?: string,
  isPrimary = false,
  order = 0
): ProductImage {
  // Support signature: (productId, variantId, url, isPrimary, order)
  if (typeof sizeOrIsPrimary === 'boolean' || (typeof fileNameOrUrl === 'string' && fileNameOrUrl.startsWith('data:'))) {
    const variantId = typeof sizeOrIsPrimary === 'boolean' ? (variantIdOrId || (urlOrVariantId.startsWith('var-') ? urlOrVariantId : undefined)) : undefined;
    const url = fileNameOrUrl.startsWith('data:') ? fileNameOrUrl : urlOrVariantId;
    const isPrim = typeof sizeOrIsPrimary === 'boolean' ? sizeOrIsPrimary : Boolean(isPrimary);
    const ord = typeof mimeTypeOrOrder === 'number' ? mimeTypeOrOrder : order;

    return {
      id: `img-${generateUUID().substring(0, 8)}`,
      productId,
      variantId,
      url,
      fileName: `image-${Date.now()}.webp`,
      fileSize: 1024,
      mimeType: 'image/webp',
      isPrimary: isPrim,
      order: ord,
      createdAt: new Date().toISOString(),
    };
  }

  return {
    id: `img-${generateUUID().substring(0, 8)}`,
    productId,
    variantId: variantIdOrId || undefined,
    url: urlOrVariantId,
    fileName: fileNameOrUrl,
    fileSize: typeof sizeOrIsPrimary === 'number' ? sizeOrIsPrimary : 1024,
    mimeType: typeof mimeTypeOrOrder === 'string' ? mimeTypeOrOrder : 'image/webp',
    isPrimary,
    order,
    createdAt: new Date().toISOString(),
  };
}
