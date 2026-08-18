import { db } from '../db/dexie';
import { ProductVariant } from '../types/productVariant';
import { ProductImage } from '../types/productMedia';

export async function getVariantsByProductId(productId: string): Promise<ProductVariant[]> {
  return await db.productVariants.where('productId').equals(productId).toArray();
}

export async function getVariantBySku(sku: string): Promise<ProductVariant | undefined> {
  return await db.productVariants.where('sku').equals(sku.toUpperCase()).first();
}

export async function getVariantByBarcode(barcode: string): Promise<ProductVariant | undefined> {
  return await db.productVariants.where('barcode').equals(barcode).first();
}

export async function getImagesByProductId(productId: string): Promise<ProductImage[]> {
  return await db.productImages.where('productId').equals(productId).sortBy('order');
}

export async function getImagesByVariantId(variantId: string): Promise<ProductImage[]> {
  return await db.productImages.where('variantId').equals(variantId).sortBy('order');
}