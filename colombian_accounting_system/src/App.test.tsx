import { describe, it, expect } from 'vitest';
import { settleDianTaxes } from './engine/taxSettlementEngine';
import { calculateTrialBalance } from './engine/balanceCalculator';
import { Voucher } from './types/accounting';

describe('Motor Contable Colombiano & DIAN', () => {
  it('Liquida IVA 19%, Retefuente 2.5% y ReteICA 9.66 por mil con precisión exacta', () => {
    const settlement = settleDianTaxes({
      subtotal: 10000000,
      ivaRate: 19,
      reteFuenteRate: 2.5,
      reteIcaPermil: 9.66,
      applyReteIva: false,
      thirdPartyType: 'DECLARANTE',
    });

    expect(settlement.subtotal).toBe(10000000);
    expect(settlement.ivaAmount).toBe(1900000);
    expect(settlement.reteFuenteAmount).toBe(250000);
    expect(settlement.reteIcaAmount).toBe(96600);
    expect(settlement.totalPayable).toBe(11553400);
    expect(settlement.totalDebits).toBe(settlement.totalCredits);
  });

  it('Valida balance de prueba con partida doble', () => {
    const mockVouchers: Voucher[] = [
      {
        id: 'TEST-1',
        consecutive: 'FV-01',
        type: 'FACTURA_VENTA',
        date: '2025-02-01',
        period: '2025-02',
        notes: 'Test',
        status: 'CONTABILIZADO',
        createdBy: 'Admin',
        createdAt: '2025-02-01',
        isLocked: false,
        lines: [
          { id: '1', accountCode: '11050501', accountName: 'Caja', thirdPartyNit: '123', thirdPartyName: 'T', concept: 'C', debit: 5000, credit: 0 },
          { id: '2', accountCode: '413505', accountName: 'Ingresos', thirdPartyNit: '123', thirdPartyName: 'T', concept: 'C', debit: 0, credit: 5000 },
        ],
      },
    ];

    const report = calculateTrialBalance(mockVouchers, '2025-02');
    const activoRow = report.find((r) => r.code === '1');
    const ingresoRow = report.find((r) => r.code === '4');

    expect(activoRow?.debits).toBe(5000);
    expect(ingresoRow?.credits).toBe(5000);
  });
});