import { VariantAttributes } from '../types/productVariant';

export function sanitizeVariantName(name: string): string {
  if (!name) return '';
  return name
    .replace(/[<>\/\\{};\[\]]/g, '')
    .trim()
    .slice(0, 100);
}

export function sanitizeVariantSku(sku: string): string {
  if (!sku) return '';
  return sku
    .toUpperCase()
    .replace(/[^A-Z0-9_-]/g, '')
    .trim()
    .slice(0, 50);
}

export function sanitizeAttributeValue(value: string): string {
  if (!value) return '';
  return value
    .replace(/[<>\/\\{}$;"']/g, '')
    .trim()
    .slice(0, 50);
}

export function sanitizeAttributes(attrs: VariantAttributes): VariantAttributes {
  const sanitized: VariantAttributes = {};
  for (const [k, v] of Object.entries(attrs)) {
    if (v && typeof v === 'string') {
      const cleanKey = k.replace(/[^a-zA-Z0-9_]/g, '').slice(0, 30);
      sanitized[cleanKey] = sanitizeAttributeValue(v);
    }
  }
  return sanitized;
}