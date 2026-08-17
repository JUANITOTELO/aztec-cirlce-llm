import { VariantAuditLog, ProductVariant } from '../types/productVariant';
import { db } from '../db/dexie';

export function createVariantAuditEntry(
  variantId: string,
  productId: string,
  action: VariantAuditLog['action'],
  userId: string,
  oldVariant?: Partial<ProductVariant>,
  newVariant?: Partial<ProductVariant>
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
    id: `val-${Date.now()}-${Math.random().toString(36).substr(2, 6)}`,
    variantId,
    productId,
    action,
    deltas,
    performedBy: userId,
    timestamp: new Date().toISOString(),
  };
}

export async function logVariantMutation(log: VariantAuditLog): Promise<void> {
  try {
    await db.variantAuditLogs.add(log);
  } catch (err) {
    console.warn('Failed to log variant audit to Dexie:', err);
  }
}