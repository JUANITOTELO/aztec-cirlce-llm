import axios from 'axios';
import { Product, SaleInvoice, LedgerEntry, UserAccount, RoleItem } from '../types/store';
import { ProductVariant } from '../types/productVariant';
import { ProductImage } from '../types/productMedia';
import { Category } from '../types/category';

const API_BASE = '/api';

export interface BackendSyncState {
  products: Product[];
  variants: ProductVariant[];
  images: ProductImage[];
  categories: Category[];
  sales: any[];
  ledgerEntries: LedgerEntry[];
  users: UserAccount[];
  roles: RoleItem[];
}

export class BackendSyncEngine {
  private static isBackendOnline = false;

  public static async checkHealth(): Promise<boolean> {
    try {
      const res = await axios.get(`${API_BASE}/health`, { timeout: 2500 });
      this.isBackendOnline = res.data?.status === 'healthy';
      return this.isBackendOnline;
    } catch {
      this.isBackendOnline = false;
      return false;
    }
  }

  public static getOnlineStatus(): boolean {
    return this.isBackendOnline;
  }

  public static async fetchAllData(): Promise<BackendSyncState | null> {
    try {
      const res = await axios.get(`${API_BASE}/sync/all`, { timeout: 4000 });
      if (res.data?.success && res.data?.data) {
        this.isBackendOnline = true;
        return res.data.data;
      }
      return null;
    } catch (err) {
      console.warn('[SyncEngine] Backend unavailable, operating in Dexie IndexedDB mode:', err);
      this.isBackendOnline = false;
      return null;
    }
  }

  public static async pushAllData(state: Partial<BackendSyncState>): Promise<boolean> {
    try {
      const res = await axios.post(`${API_BASE}/sync/all`, state, { timeout: 5000 });
      return !!res.data?.success;
    } catch (err) {
      console.warn('[SyncEngine] Failed to push full state to backend:', err);
      return false;
    }
  }

  public static async saveProduct(product: Product): Promise<boolean> {
    try {
      await axios.post(`${API_BASE}/products`, product, { timeout: 3000 });
      return true;
    } catch (err) {
      console.warn('[SyncEngine] Product save to backend queued:', err);
      return false;
    }
  }

  public static async deleteProduct(productId: string): Promise<boolean> {
    try {
      await axios.delete(`${API_BASE}/products/${productId}`, { timeout: 3000 });
      return true;
    } catch (err) {
      console.warn('[SyncEngine] Product deletion to backend failed:', err);
      return false;
    }
  }

  public static async saveVariant(productId: string, variant: ProductVariant): Promise<boolean> {
    try {
      await axios.post(`${API_BASE}/products/${productId}/variants`, variant, { timeout: 3000 });
      return true;
    } catch (err) {
      console.warn('[SyncEngine] Variant save to backend queued:', err);
      return false;
    }
  }

  public static async saveImage(productId: string, image: ProductImage): Promise<boolean> {
    try {
      await axios.post(`${API_BASE}/products/${productId}/images`, image, { timeout: 4000 });
      return true;
    } catch (err) {
      console.warn('[SyncEngine] Image save to backend queued:', err);
      return false;
    }
  }

  public static async saveCategory(category: Category): Promise<boolean> {
    try {
      await axios.post(`${API_BASE}/categories`, category, { timeout: 3000 });
      return true;
    } catch (err) {
      console.warn('[SyncEngine] Category save to backend queued:', err);
      return false;
    }
  }

  public static async saveSale(invoice: SaleInvoice): Promise<boolean> {
    try {
      const res = await axios.post(`${API_BASE}/sales`, invoice, { timeout: 4000 });
      return !!res.data?.success;
    } catch (err) {
      console.warn('[SyncEngine] Sale record to backend queued:', err);
      return false;
    }
  }
}
