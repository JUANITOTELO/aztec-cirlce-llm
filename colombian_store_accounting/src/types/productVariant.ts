export interface VariantAttributes {
  size?: string;
  color?: string;
  flavor?: string;
  presentation?: string;
  [key: string]: string | undefined;
}

export interface ProductVariant {
  id: string;
  productId: string;
  sku: string;
  name: string;
  barcode?: string;
  price: number;
  cost: number;
  stock: number;
  minStock: number;
  attributes: VariantAttributes;
  isDefault?: boolean;
  isActive?: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface ProductVariantFormData {
  sku: string;
  name: string;
  barcode?: string;
  price: number;
  cost: number;
  stock: number;
  minStock: number;
  attributes?: VariantAttributes;
  isDefault?: boolean;
  isActive?: boolean;
}

export interface VariantAuditLog {
  id: string;
  variantId?: string;
  productId: string;
  action: 'CREATED' | 'UPDATED' | 'DELETED' | 'STOCK_ADJUSTED' | 'CREATE' | 'UPDATE' | 'DELETE';
  deltas?: Record<string, { old: any; new: any }>;
  changes?: any;
  performedBy?: string;
  userId?: string;
  timestamp: string;
}

export interface ProductVariantPermissions {
  canCreateVariant: boolean;
  canEditVariant: boolean;
  canDeleteVariant: boolean;
  canUploadImages: boolean;
  canDeleteImages: boolean;
}