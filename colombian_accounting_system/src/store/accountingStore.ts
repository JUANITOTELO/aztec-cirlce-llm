import { create } from 'zustand';
import { Voucher, VoucherStatus } from '../types/accounting';

interface AccountingState {
  vouchers: Voucher[];
  lockedPeriods: string[];
  activePeriod: string;
  addVoucher: (voucher: Voucher) => { success: boolean; error?: string };
  updateVoucherStatus: (id: string, newStatus: VoucherStatus, userId: string) => { success: boolean; error?: string };
  togglePeriodLock: (period: string) => void;
  setActivePeriod: (period: string) => void;
}

const INITIAL_VOUCHERS: Voucher[] = [
  {
    id: 'V-001',
    consecutive: 'FV-2025-0001',
    type: 'FACTURA_VENTA',
    date: '2025-02-15',
    period: '2025-02',
    notes: 'Factura venta de servicios tecnológicos',
    status: 'CONTABILIZADO',
    createdBy: 'USR-002 (Auxiliar)',
    reviewedBy: 'USR-001 (Contador)',
    approvedBy: 'USR-000 (Admin)',
    createdAt: '2025-02-15 09:30:00',
    isLocked: false,
    lines: [
      { id: '1', accountCode: '13050501', accountName: 'Cartera Clientes Comerciales', thirdPartyNit: '860001234-5', thirdPartyName: 'Soluciones Globales SAS', concept: 'Venta software', debit: 11600000, credit: 0 },
      { id: '135515', accountCode: '135515', accountName: 'Retención en la Fuente 2.5%', thirdPartyNit: '860001234-5', thirdPartyName: 'Soluciones Globales SAS', concept: 'ReteFuente 2.5%', debit: 250000, credit: 0 },
      { id: '135518', accountCode: '135518', accountName: 'ReteICA 9.66/1000', thirdPartyNit: '860001234-5', thirdPartyName: 'Soluciones Globales SAS', concept: 'ReteICA 9.66/1000', debit: 96600, credit: 0 },
      { id: '2', accountCode: '240801', accountName: 'IVA Generado 19%', thirdPartyNit: '860001234-5', thirdPartyName: 'Soluciones Globales SAS', concept: 'IVA 19% venta', debit: 0, credit: 1900000 },
      { id: '3', accountCode: '413505', accountName: 'Venta de Productos Comerciales', thirdPartyNit: '860001234-5', thirdPartyName: 'Soluciones Globales SAS', concept: 'Ingreso servicios', debit: 0, credit: 10046600 },
    ],
  },
];

export const useAccountingStore = create<AccountingState>((set, get) => ({
  vouchers: INITIAL_VOUCHERS,
  lockedPeriods: ['2025-01'],
  activePeriod: '2025-02',
  setActivePeriod: (period) => set({ activePeriod: period }),
  togglePeriodLock: (period) =>
    set((state) => ({
      lockedPeriods: state.lockedPeriods.includes(period)
        ? state.lockedPeriods.filter((p) => p !== period)
        : [...state.lockedPeriods, period],
    })),
  addVoucher: (voucher) => {
    const { lockedPeriods } = get();
    if (lockedPeriods.includes(voucher.period)) {
      return { success: false, error: `El periodo ${voucher.period} se encuentra bloqueado legalmente.` };
    }
    const totalDebits = voucher.lines.reduce((s, l) => s + l.debit, 0);
    const totalCredits = voucher.lines.reduce((s, l) => s + l.credit, 0);
    if (Math.abs(totalDebits - totalCredits) > 0.01) {
      return { success: false, error: 'Descuadre contable: Los débitos deben ser exactamente iguales a los créditos.' };
    }
    set((state) => ({ vouchers: [voucher, ...state.vouchers] }));
    return { success: true };
  },
  updateVoucherStatus: (id, newStatus, userId) => {
    const { vouchers, lockedPeriods } = get();
    const target = vouchers.find((v) => v.id === id);
    if (!target) return { success: false, error: 'Comprobante no encontrado' };
    if (lockedPeriods.includes(target.period)) {
      return { success: false, error: 'Periodo contable cerrado. No se permiten modificaciones.' };
    }
    set((state) => ({
      vouchers: state.vouchers.map((v) =>
        v.id === id ? { ...v, status: newStatus, ...(newStatus === 'APROBADO' ? { approvedBy: userId } : {}) } : v
      ),
    }));
    return { success: true };
  },
}));