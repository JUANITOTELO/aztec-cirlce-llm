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
    const itemSubtotal = (item.product.price / (1 + item.product.ivaRate)) * item.quantity;
    const itemIva = (item.product.price - (item.product.price / (1 + item.product.ivaRate))) * item.quantity;
    subtotal += itemSubtotal;
    iva += itemIva;
  }

  const total = subtotal + iva;
  return {
    subtotal: Math.round(subtotal),
    iva: Math.round(iva),
    total: Math.round(total),
  };
}
