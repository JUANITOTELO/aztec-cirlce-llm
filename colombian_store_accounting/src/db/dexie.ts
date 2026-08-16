import Dexie, { Table } from 'dexie';
import { Category, CategoryAuditLog } from '../types/category';
import { INITIAL_CATEGORIES } from '../constants/mockCategories';

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
  type: 'SALE_INVOICE' | 'STOCK_ADJUSTMENT' | 'CATEGORY_MUTATION';
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
  }
}

export const db = new AppDB();

export async function addTransactionToQueue(type: TransactionQueueItem['type'], payload: any): Promise<number> {
  return await db.transactionQueue.add({
    type,
    payload,
    status: 'PENDING',
    createdAt: new Date().toISOString(),
    retryCount: 0,
  });
}
