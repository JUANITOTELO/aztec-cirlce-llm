import Dexie, { Table } from 'dexie';
import { Category, CategoryAuditLog } from '../types/category';
import { ProductVariant, VariantAuditLog } from '../types/productVariant';
import { ProductImage } from '../types/productMedia';
import { INITIAL_CATEGORIES } from '../constants/mockCategories';
import { INITIAL_VARIANTS, INITIAL_PRODUCT_IMAGES } from '../constants/mockVariants';

const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

export interface TransactionPayload {
  consecutive: string;
  total: number;
  paymentMethod: string;
  customerName: string;
  customerDoc: string;
  itemsCount: number;
  items: any[];
  subtotal: number;
  taxTotal: number;
  date: string;
}

export interface TransactionQueueItem {
  id?: number;
  type: 'SALE_INVOICE' | 'STOCK_ADJUSTMENT' | 'CATEGORY_MUTATION' | 'VARIANT_MUTATION';
  payload: any;
  status: 'PENDING' | 'SYNCED' | 'FAILED';
  createdAt: string;
  retryCount: number;
  lastError?: string;
}

export class AppDB extends Dexie {
  transactionQueue!: Table<TransactionQueueItem, number>;
  categories!: Table<Category, string>;
  categoryAuditLogs!: Table<CategoryAuditLog, string>;
  productVariants!: Table<ProductVariant, string>;
  productImages!: Table<ProductImage, string>;
  variantAuditLogs!: Table<VariantAuditLog, string>;

  constructor() {
    super('AppDB');

    this.version(4).stores({
      transactionQueue: '++id, status, type, createdAt',
      categories: 'id, name, ledgerAccountCode, isDeleted',
      categoryAuditLogs: '++id, categoryId, action, timestamp, userId, [categoryId+timestamp]',
      productVariants: 'id, productId, sku, barcode, [productId+sku]',
      productImages: 'id, productId, variantId, order_pos, fileHash, [productId+variantId+order_pos]',
      variantAuditLogs: 'id, variantId, productId, action, timestamp, [productId+timestamp]',
    });

    this.version(5).upgrade(async (tx) => {
      try {
        const images = tx.table('productImages');
        const all = await images.toArray();
        await Promise.all(
          all.map((img) => images.update(img.id, { order_pos: img.order_pos || 1 }))
        );
      } catch (err) {
        console.error('Dexie v5 migration backfill error:', err);
      }
    });

    this.on('populate', async () => {
      try {
        await this.categories.bulkAdd(INITIAL_CATEGORIES);
        await this.productVariants.bulkAdd(INITIAL_VARIANTS);
        await this.productImages.bulkAdd(INITIAL_PRODUCT_IMAGES);
      } catch (err) {
        console.error('Dexie initial seed error:', err);
      }
    });
  }
}

export const db = new AppDB();

export async function deleteProductVariantsWithCascade(productId: string): Promise<void> {
  await db.transaction('rw', db.productVariants, db.productImages, db.variantAuditLogs, async () => {
    await db.productVariants.where('productId').equals(productId).delete();
    await db.productImages.where('productId').equals(productId).delete();
    await db.variantAuditLogs.where('productId').equals(productId).delete();
  });
}

export const deleteProductWithCascade = deleteProductVariantsWithCascade;

export async function deleteVariantWithCascade(variantId: string): Promise<void> {
  await db.transaction('rw', db.productVariants, db.productImages, db.variantAuditLogs, async () => {
    await db.productVariants.delete(variantId);
    await db.productImages.where('variantId').equals(variantId).delete();
    await db.variantAuditLogs.where('variantId').equals(variantId).delete();
  });
}

export async function addTransactionToQueue(type: TransactionQueueItem['type'], payload: any): Promise<number> {
  return await db.transactionQueue.add({
    type,
    payload,
    status: 'PENDING',
    createdAt: new Date().toISOString(),
    retryCount: 0,
  });
}

export async function processTransactionQueue(): Promise<void> {
  const pendingItems = await db.transactionQueue
    .where('status')
    .equals('PENDING')
    .toArray();

  for (const item of pendingItems) {
    if (item.retryCount >= MAX_RETRIES) {
      await db.transactionQueue.update(item.id!, { status: 'FAILED' });
      console.error(`[Queue] Max retries exceeded for transaction ${item.id}`);
      continue;
    }

    try {
      // Simulate sync to backend (replace with actual API call)
      await new Promise((resolve) => setTimeout(resolve, 100));
      await db.transactionQueue.update(item.id!, { status: 'SYNCED' });
      console.log(`[Queue] Transaction ${item.id} synced successfully`);
    } catch (error) {
      const delay = RETRY_DELAY * Math.pow(2, item.retryCount);
      await db.transactionQueue.update(item.id!, {
        retryCount: item.retryCount + 1,
        lastError: error instanceof Error ? error.message : 'Unknown error',
      });
      console.warn(`[Queue] Retry ${item.retryCount + 1} for transaction ${item.id} in ${delay}ms`);
    }
  }
}
