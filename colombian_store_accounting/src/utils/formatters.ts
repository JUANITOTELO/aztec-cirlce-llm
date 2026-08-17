/**
 * Currency & Tax formatting utilities for Colombian Accounting
 */

export function formatCOP(amount: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function formatPercent(rate: number): string {
  return `${(rate * 100).toFixed(0)}%`;
}

export function calculateCartTotals(items: { product: { price: number; ivaRate: number }; quantity: number }[]) {
  let subtotal = 0;
  let iva = 0;

  for (const item of items) {
    const rate = item.product.ivaRate ?? 0;
    const itemSubtotal = Math.round((item.product.price / (1 + rate)) * item.quantity);
    const itemIva = Math.round((item.product.price * item.quantity) - itemSubtotal);
    subtotal += itemSubtotal;
    iva += itemIva;
  }

  return {
    subtotal,
    iva,
    taxTotal: iva,
    total: subtotal + iva,
  };
}

export function newDateIso(): string {
  return new Date().toISOString();
}
