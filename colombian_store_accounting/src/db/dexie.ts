import Dexie, { Table } from 'dexie';
import { Category, CategoryAuditLog } from '../types/category';
import { ProductVariant, VariantAuditLog } from '../types/productVariant';
import { ProductImage } from '../types/productMedia';
import { INITIAL_CATEGORIES } from '../constants/mockCategories';
import { INITIAL_VARIANTS, INITIAL_PRODUCT_IMAGES } from '../constants/mockVariants';

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
    super('AztecDB');
    this.version(1).stores({
      transactionQueue: '++id, status, type, createdAt',
    });
    this.version(2).stores({
      transactionQueue: '++id, status, type, createdAt',
      categories: 'id, name, ledgerAccountCode, isDeleted',
      categoryAuditLogs: '++id, categoryId, action, timestamp, userId, [categoryId+timestamp]',
    }).upgrade(async (tx) => {
      try {
        const count = await tx.table('categories').count();
        if (count === 0) {
          await tx.table('categories').bulkAdd(INITIAL_CATEGORIES);
        }
      } catch (err) {
        console.error('Dexie v2 categories migration error:', err);
      }
    });
    this.version(3).stores({
      transactionQueue: '++id, status, type, createdAt',
      categories: 'id, name, ledgerAccountCode, isDeleted',
      categoryAuditLogs: '++id, categoryId, action, timestamp, userId, [categoryId+timestamp]',
      productVariants: 'id, productId, sku, barcode, [productId+sku]',
      productImages: 'id, productId, variantId, order, [productId+variantId+order]',
      variantAuditLogs: 'id, variantId, productId, action, timestamp, [productId+timestamp]',
    }).upgrade(async (tx) => {
      try {
        const varCount = await tx.table('productVariants').count();
        if (varCount === 0) {
          await tx.table('productVariants').bulkAdd(INITIAL_VARIANTS);
        }
        const imgCount = await tx.table('productImages').count();
        if (imgCount === 0) {
          await tx.table('productImages').bulkAdd(INITIAL_PRODUCT_IMAGES);
        }
      } catch (err) {
        console.error('Dexie v3 variants/images migration error:', err);
      }
    });
  }
}

export const db = new AppDB();

export async function deleteProductWithCascade(productId: string): Promise<void> {
  await db.transaction('rw', db.productVariants, db.productImages, db.variantAuditLogs, async () => {
    await db.productVariants.where('productId').equals(productId).delete();
    await db.productImages.where('productId').equals(productId).delete();
    await db.variantAuditLogs.where('productId').equals(productId).delete();
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
