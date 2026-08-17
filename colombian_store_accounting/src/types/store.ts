/**
 * TypeScript Interfaces for Colombian Store & Accounting Management System
 */

import { ProductVariant } from './productVariant';
import { ProductImage } from './productMedia';

export type AppModule = 'pos' | 'products' | 'inventory' | 'ledger' | 'dian' | 'puc' | 'users' | 'multimedia';

export interface RoleItem {
  id: string;
  name: string;
  description: string;
  modules: AppModule[];
  isSystem?: boolean;
}

export interface UserAccount {
  id: string;
  name: string;
  email: string;
  roleId: string;
  role?: string;
  password?: string;
  permissions?: string[];
  isActive?: boolean;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  category: string;
  price: number;
  cost: number;
  stock: number;
  minStock: number;
  ivaRate: number;
  barcode?: string;
  image?: string;
  imageUrl?: string;
  variants?: ProductVariant[];
  images?: ProductImage[];
}

export interface CartItem {
  product: Product;
  quantity: number;
  variantId?: string;
  variantSku?: string;
  unitCost?: number;
  unitPrice?: number;
}

export interface LedgerEntry {
  id: string;
  transactionId: string;
  date: string;
  pucCode: string;
  pucName: string;
  description: string;
  debit: number;
  credit: number;
}

export interface PucAccount {
  code: string;
  name: string;
  type: 'Activo' | 'Pasivo' | 'Patrimonio' | 'Ingresos' | 'Gastos' | 'Costos';
  level: number; // 1: Clase, 2: Grupo, 4: Cuenta, 6: Subcuenta
}

export interface SaleInvoice {
  id: string;
  consecutive: string;
  date: string;
  customerName: string;
  customerDoc: string;
  paymentMethod: 'Efectivo' | 'Tarjeta' | 'Nequi / Daviplata';
  subtotal: number;
  iva: number;
  total: number;
  items: CartItem[];
  variantDetails?: Record<string, any>;
}
