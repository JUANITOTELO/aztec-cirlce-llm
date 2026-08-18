export interface TaxCalculationParams {
  subtotal: number;
  ivaRate: number;
  reteFuenteRate: number;
  reteIcaPermil: number;
  applyReteIva: boolean;
  thirdPartyType: 'DECLARANTE' | 'NO_DECLARANTE' | 'GRAN_CONTRIBUYENTE' | 'AUTORRETENEDOR';
}

export interface TaxSettlementResult {
  subtotal: number;
  ivaAmount: number;
  reteFuenteAmount: number;
  reteIcaAmount: number;
  reteIvaAmount: number;
  totalPayable: number;
  totalDebits: number;
  totalCredits: number;
}