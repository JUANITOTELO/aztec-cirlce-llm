export type VoucherType = 'FACTURA_VENTA' | 'COMPROBANTE_INGRESO' | 'COMPROBANTE_EGRESO' | 'NOTA_CONTABLE' | 'NOMINA';
export type VoucherStatus = 'BORRADOR' | 'REVISADO' | 'APROBADO' | 'CONTABILIZADO' | 'ANULADO';

export interface AccountingEntryLine {
  id: string;
  accountCode: string;
  accountName: string;
  thirdPartyNit: string;
  thirdPartyName: string;
  concept: string;
  debit: number;
  credit: number;
  baseAmount?: number;
}

export interface Voucher {
  id: string;
  consecutive: string;
  type: VoucherType;
  date: string;
  period: string;
  notes: string;
  lines: AccountingEntryLine[];
  status: VoucherStatus;
  createdBy: string;
  reviewedBy?: string;
  approvedBy?: string;
  createdAt: string;
  isLocked: boolean;
}