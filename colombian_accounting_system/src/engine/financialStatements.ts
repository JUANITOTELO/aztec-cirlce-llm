import { calculateTrialBalance, AccountBalanceReportRow } from './balanceCalculator';
import { Voucher } from '../types/accounting';
import { roundDian } from '../utils/mathPrecision';

export interface IncomeStatement {
  grossRevenue: number;
  costOfSales: number;
  grossProfit: number;
  operatingExpenses: number;
  netOperatingIncome: number;
  rows: AccountBalanceReportRow[];
}

export function generateIncomeStatement(vouchers: Voucher[], period?: string): IncomeStatement {
  const rows = calculateTrialBalance(vouchers, period);
  
  const revenueRow = rows.find(r => r.code === '4');
  const grossRevenue = revenueRow ? revenueRow.credits - revenueRow.debits : 0;

  const costsRow = rows.find(r => r.code === '6');
  const costOfSales = costsRow ? costsRow.debits - costsRow.credits : 0;

  const grossProfit = roundDian(grossRevenue - costOfSales);

  const expensesRow = rows.find(r => r.code === '5');
  const operatingExpenses = expensesRow ? expensesRow.debits - expensesRow.credits : 0;

  const netOperatingIncome = roundDian(grossProfit - operatingExpenses);

  return {
    grossRevenue: roundDian(grossRevenue),
    costOfSales: roundDian(costOfSales),
    grossProfit,
    operatingExpenses: roundDian(operatingExpenses),
    netOperatingIncome,
    rows: rows.filter(r => ['4', '5', '6'].includes(r.code[0])),
  };
}