import { TaxCalculationParams, TaxSettlementResult } from '../types/tax';
import { roundDian, toCents, fromCents } from '../utils/mathPrecision';

export function settleDianTaxes(params: TaxCalculationParams): TaxSettlementResult {
  const subtotalCents = toCents(params.subtotal);
  
  // Calculate IVA (e.g. 19%)
  const ivaCents = Math.round(subtotalCents * (params.ivaRate / 100));
  
  // Retención en la Fuente (percentage)
  const reteFuenteCents = Math.round(subtotalCents * (params.reteFuenteRate / 100));
  
  // ReteICA (per-mil: e.g. 9.66 per thousand => 0.00966)
  const reteIcaCents = Math.round(subtotalCents * (params.reteIcaPermil / 1000));
  
  // ReteIVA (typically 15% of the IVA amount if applicable)
  const reteIvaCents = params.applyReteIva ? Math.round(ivaCents * 0.15) : 0;
  
  // Total payable after retentions
  const totalPayableCents = subtotalCents + ivaCents - reteFuenteCents - reteIcaCents - reteIvaCents;
  
  const subtotal = fromCents(subtotalCents);
  const ivaAmount = fromCents(ivaCents);
  const reteFuenteAmount = fromCents(reteFuenteCents);
  const reteIcaAmount = fromCents(reteIcaCents);
  const reteIvaAmount = fromCents(reteIvaCents);
  const totalPayable = fromCents(totalPayableCents);
  
  return {
    subtotal,
    ivaAmount,
    reteFuenteAmount,
    reteIcaAmount,
    reteIvaAmount,
    totalPayable,
    totalDebits: roundDian(totalPayable + reteFuenteAmount + reteIcaAmount + reteIvaAmount),
    totalCredits: roundDian(subtotal + ivaAmount),
  };
}