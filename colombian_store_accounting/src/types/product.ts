export type ProductCategory = string;

export type AdjustmentType = 'INFLOW' | 'OUTFLOW' | 'ADD' | 'REMOVE';

export type AdjustmentReason =
  | 'PURCHASE'
  | 'SALE_RETURN'
  | 'DAMAGED'
  | 'EXPIRED'
  | 'THEFT_OR_LOSS'
  | 'INVENTORY_AUDIT'
  | 'INITIAL_COUNT'
  | 'COMPRA_PROVEEDOR'
  | 'MERMA_DETERIORO'
  | 'AJUSTE_FISICO'
  | 'DEVOLUCION_CLIENTE'
  | 'OTRO';

export interface ProductPricingRecord {
  id: string;
  productId: string;
  sku?: string;
  oldPrice: number;
  newPrice: number;
  oldCost: number;
  newCost: number;
  oldIvaRate?: number;
  newIvaRate?: number;
  changedAt: string;
  changedBy: string;
  reason?: string;
}

export interface StockAdjustmentPayload {
  id?: string;
  productId: string;
  sku?: string;
  productName?: string;
  type?: AdjustmentType;
  adjustmentType?: AdjustmentType;
  quantity: number;
  unitCost?: number;
  reason?: AdjustmentReason;
  notes?: string;
  performedBy?: string;
  adjustedBy?: string;
  adjustedAt?: string;
}

export interface ProductFormData {
  sku: string;
  name: string;
  category: ProductCategory;
  price: number;
  cost: number;
  stock: number;
  minStock: number;
  ivaRate: number;
  barcode: string;
}

export interface ProductValidationError {
  field: keyof ProductFormData;
  message: string;
}

export interface ProductPermissions {
  canViewCost: boolean;
  canEditProduct: boolean;
  canCreateProduct: boolean;
  canDeleteProduct: boolean;
  canAdjustStock: boolean;
  canViewPricingHistory: boolean;
}
