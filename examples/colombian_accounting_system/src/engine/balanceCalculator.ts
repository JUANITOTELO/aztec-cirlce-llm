import { AccountingEntryLine, Voucher } from '../types/accounting';
import { PUC_CATALOG } from '../constants/pucColombia';
import { roundDian } from '../utils/mathPrecision';

export interface AccountBalanceReportRow {
  code: string;
  name: string;
  level: string;
  initialBalance: number;
  debits: number;
  credits: number;
  finalBalance: number;
}

export function calculateTrialBalance(vouchers: Voucher[], period?: string): AccountBalanceReportRow[] {
  const activeVouchers = vouchers.filter(v => v.status === 'CONTABILIZADO' && (!period || v.period === period));
  const movementsMap = new Map<string, { debits: number; credits: number }>();

  activeVouchers.forEach(v => {
    v.lines.forEach(line => {
      const current = movementsMap.get(line.accountCode) || { debits: 0, credits: 0 };
      movementsMap.set(line.accountCode, {
        debits: current.debits + line.debit,
        credits: current.credits + line.credit,
      });
    });
  });

  return PUC_CATALOG.map(acc => {
    // Aggregate account movements and its sub-branches
    let debits = 0;
    let credits = 0;
    movementsMap.forEach((val, code) => {
      if (code.startsWith(acc.code)) {
        debits += val.debits;
        credits += val.credits;
      }
    });

    const deb = roundDian(debits);
    const cred = roundDian(credits);
    const finalBalance = acc.nature === 'DEBITO' ? roundDian(deb - cred) : roundDian(cred - deb);

    return {
      code: acc.code,
      name: acc.name,
      level: acc.level,
      initialBalance: 0,
      debits: deb,
      credits: cred,
      finalBalance,
    };
  }).filter(r => r.debits > 0 || r.credits > 0 || r.level === 'CLASE');
}