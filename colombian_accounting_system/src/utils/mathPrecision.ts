/**
 * Arbitrary Precision Decimal Helpers using integer cents arithmetic
 * Mitigates DIAN rounding divergence.
 */
export function toCents(amount: number): number {
  return Math.round((amount + Number.EPSILON) * 100);
}

export function fromCents(cents: number): number {
  return cents / 100;
}

export function roundDian(amount: number): number {
  return Math.round((amount + Number.EPSILON) * 100) / 100;
}

export function formatCop(amount: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}