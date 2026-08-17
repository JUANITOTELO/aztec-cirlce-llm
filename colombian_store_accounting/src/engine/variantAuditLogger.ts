import { VariantAuditLog, ProductVariant } from '../types/productVariant';
import { db } from '../db/dexie';

export function createVariantAuditEntry(
  variantId: string,
  productId: string,
  action: VariantAuditLog['action'],
  userId: string = 'system',
  oldVariant?: Partial<ProductVariant> | Record<string, any>,
  newVariant?: Partial<ProductVariant> | Record<string, any>
): VariantAuditLog {
  const deltas: Record<string, { old: any; new: any }> = {};
  if (oldVariant && newVariant) {
    const keys = new Set([...Object.keys(oldVariant), ...Object.keys(newVariant)]);
    keys.forEach((key) => {
      const oldVal = (oldVariant as any)[key];
      const newVal = (newVariant as any)[key];
      if (oldVal !== newVal) {
        deltas[key] = { old: oldVal, new: newVal };
      }
    });
  }
  return {
    id: `val-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`,
    variantId,
    productId,
    action,
    deltas,
    performedBy: typeof userId === 'string' ? userId : (userId as any)?.user || 'system',
    userId: typeof userId === 'string' ? userId : (userId as any)?.user || 'system',
    details: typeof oldVariant === 'object' && !newVariant ? JSON.stringify(oldVariant) : undefined,
    metadata: typeof oldVariant === 'object' ? (oldVariant as Record<string, any>) : undefined,
    timestamp: new Date().toISOString(),
  };
}

export async function logVariantMutation(
  variantIdOrEntry: string | Partial<VariantAuditLog>,
  productId?: string,
  action?: VariantAuditLog['action'],
  userIdOrDetails?: any,
  oldVariant?: Partial<ProductVariant>,
  newVariant?: Partial<ProductVariant>
): Promise<void> {
  try {
    let entry: VariantAuditLog;
    if (typeof variantIdOrEntry === 'object' && variantIdOrEntry !== null) {
      entry = {
        id: variantIdOrEntry.id || `val-${Date.now()}-${Math.random().toString(36).substring(2, 8)}`,
        variantId: variantIdOrEntry.variantId || 'product_global',
        productId: variantIdOrEntry.productId || '',
        action: variantIdOrEntry.action || 'UPDATE',
        deltas: variantIdOrEntry.deltas || {},
        performedBy: variantIdOrEntry.performedBy || variantIdOrEntry.userId || 'system',
        userId: variantIdOrEntry.userId || variantIdOrEntry.performedBy || 'system',
        details: variantIdOrEntry.details,
        metadata: variantIdOrEntry.metadata,
        timestamp: variantIdOrEntry.timestamp || new Date().toISOString(),
      };
    } else {
      entry = createVariantAuditEntry(
        String(variantIdOrEntry),
        productId || '',
        action || 'UPDATE',
        typeof userIdOrDetails === 'string' ? userIdOrDetails : (userIdOrDetails?.user || 'system'),
        typeof userIdOrDetails === 'object' ? userIdOrDetails : oldVariant,
        newVariant
      );
    }
    await db.variantAuditLogs.add(entry);
  } catch (err) {
    console.warn('Failed to log variant audit to Dexie:', err);
  }
}
