import { LedgerEntry, Product, SaleInvoice } from '../types/store';
import { StockAdjustmentPayload, ProductPricingRecord } from '../types/product';
import { Category } from '../types/category';
import { resolveLedgerAccount } from './categoryConstraints';

/**
 * Orchestrates Colombian PUC Accounting Entries for Inventory Operations:
 * PUC 1435: Mercancías no fabricadas por la empresa (Activo)
 * PUC 2205: Proveedores Nacionales (Pasivo)
 * PUC 6135: Comercio al por mayor y al por menor (Costo de Ventas)
 * PUC 5315: Gastos extraordinarios / Pérdida en inventario (Gasto)
 * PUC 4135: Ingresos operacionales por venta (Ingreso)
 * PUC 2408: Impuesto sobre las ventas por pagar (IVA)
 * PUC 1105: Caja General (Efectivo)
 * PUC 1110: Bancos Nacionales (Tarjeta / Transferencia)
 */
export class ProductLedgerOrchestrator {
  static emitStockAdjustment(adjustment: StockAdjustmentPayload): LedgerEntry[] {
    const unitCost = adjustment.unitCost ?? 0;
    const totalCost = Math.round(adjustment.quantity * unitCost);
    const timestamp = adjustment.adjustedAt || new Date().toISOString();
    const txId = adjustment.id ? `ADJ-${adjustment.id}` : `ADJ-${Date.now()}`;
    const isAdd = adjustment.adjustmentType === 'ADD' || adjustment.type === 'INFLOW';
    const prodName = adjustment.productName || 'Producto';

    if (totalCost <= 0) return [];

    if (isAdd) {
      const isSupplierPurchase = adjustment.reason === 'COMPRA_PROVEEDOR' || adjustment.reason === 'PURCHASE';
      const counterPuc = isSupplierPurchase ? '220505' : '110505';
      const counterName = isSupplierPurchase ? 'Proveedores Nacionales' : 'Caja General (Ajuste)';

      return [
        {
          id: `ent-${Date.now()}-1`,
          transactionId: txId,
          date: timestamp,
          pucCode: '143501',
          pucName: 'Mercancías no Fabricadas por la Empresa',
          description: `Entrada Stock: ${prodName} (${adjustment.reason || 'Ingreso'})`,
          debit: totalCost,
          credit: 0,
        },
        {
          id: `ent-${Date.now()}-2`,
          transactionId: txId,
          date: timestamp,
          pucCode: counterPuc,
          pucName: counterName,
          description: `Contrapartida Entrada Stock: ${prodName}`,
          debit: 0,
          credit: totalCost,
        },
      ];
    } else {
      const isDamage = adjustment.reason === 'MERMA_DETERIORO' || adjustment.reason === 'DAMAGED' || adjustment.reason === 'EXPIRED';
      const lossPuc = isDamage ? '531515' : '613505';
      const lossName = isDamage ? 'Pérdida por Merma o Deterioro de Inventario' : 'Costo de Ventas - Ajuste Inventario';

      return [
        {
          id: `ent-${Date.now()}-1`,
          transactionId: txId,
          date: timestamp,
          pucCode: lossPuc,
          pucName: lossName,
          description: `Gasto/Pérdida Stock: ${prodName} (${adjustment.reason || 'Salida'})`,
          debit: totalCost,
          credit: 0,
        },
        {
          id: `ent-${Date.now()}-2`,
          transactionId: txId,
          date: timestamp,
          pucCode: '143501',
          pucName: 'Mercancías no Fabricadas por la Empresa',
          description: `Descargue Inventario: ${prodName}`,
          debit: 0,
          credit: totalCost,
        },
      ];
    }
  }

  static generateSaleEntries(invoice: SaleInvoice, categories?: Category[]): LedgerEntry[] {
    const entries: LedgerEntry[] = [];
    const now = invoice.date || new Date().toISOString();
    const txId = invoice.consecutive;

    const cashPuc = invoice.paymentMethod === 'Efectivo' ? '110505' : '111005';
    const cashName = invoice.paymentMethod === 'Efectivo' ? 'Caja General' : 'Bancos Nacionales';

    // 1. Débito a Caja o Bancos
    entries.push({
      id: `led-${Date.now()}-1`,
      transactionId: txId,
      date: now,
      pucCode: cashPuc,
      pucName: cashName,
      description: `Venta POS #${txId} - ${invoice.customerName || 'Consumidor Final'}`,
      debit: invoice.total,
      credit: 0,
    });

    // 2. Crédito a IVA generado (si aplica)
    const taxTotal = invoice.iva || 0;
    if (taxTotal > 0) {
      entries.push({
        id: `led-${Date.now()}-2`,
        transactionId: txId,
        date: now,
        pucCode: '240805',
        pucName: 'Impuesto sobre las ventas por pagar (IVA)',
        description: `IVA generado en Venta POS #${txId}`,
        debit: 0,
        credit: taxTotal,
      });
    }

    // 3. Crédito a Ingresos Operacionales (PUC 4135)
    const calculatedNetRevenue = invoice.subtotal || (invoice.total - taxTotal);
    const revenueAccount = categories && categories.length > 0 && invoice.items?.[0]?.product?.category
      ? resolveLedgerAccount(invoice.items[0].product.category, categories)
      : { code: '413505', name: 'Comercio al por mayor y al por menor' };

    entries.push({
      id: `led-${Date.now()}-3`,
      transactionId: txId,
      date: now,
      pucCode: revenueAccount.code,
      pucName: revenueAccount.name,
      description: `Ingreso operacional por venta POS #${txId}`,
      debit: 0,
      credit: calculatedNetRevenue,
    });

    return entries;
  }

  static createPricingAuditRecord(
    original: Product,
    updated: Partial<Product>,
    userName: string,
    reason: string
  ): ProductPricingRecord {
    return {
      id: `price-aud-${Date.now()}`,
      productId: original.id,
      sku: original.sku,
      oldPrice: original.price,
      newPrice: updated.price ?? original.price,
      oldCost: original.cost,
      newCost: updated.cost ?? original.cost,
      oldIvaRate: original.ivaRate,
      newIvaRate: updated.ivaRate ?? original.ivaRate,
      changedBy: userName || 'Sistema',
      changedAt: new Date().toISOString(),
      reason: reason || 'Actualización de catálogo',
    };
  }
}
