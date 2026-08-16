<?php
declare(strict_types=1);

namespace Sifco\Services;

use PDO;
use RuntimeException;

class VoucherService {
    public function __construct(private PDO $pdo) {}

    public function createVoucher(string $companyId, string $voucherType, string $date, string $notes, array $lines, string $userId): string {
        $period = substr($date, 0, 7);
        
        // 1. Verify period is not closed
        $periodStmt = $this->pdo->prepare("SELECT is_closed FROM accounting_periods WHERE company_id = ? AND period = ?");
        $periodStmt->execute([$companyId, $period]);
        $isClosed = $periodStmt->fetchColumn();
        if ($isClosed === 1 || $isClosed === '1') {
            throw new RuntimeException("Period {$period} is locked/closed.");
        }

        // 2. Validate double-entry equality with bcmath
        $totalDebit = '0.0000';
        $totalCredit = '0.0000';
        foreach ($lines as $line) {
            $totalDebit = bcadd($totalDebit, (string)($line['debit'] ?? '0'), 4);
            $totalCredit = bcadd($totalCredit, (string)($line['credit'] ?? '0'), 4);
        }

        if (bccomp($totalDebit, $totalCredit, 2) !== 0) {
            throw new RuntimeException("Double entry unbalanced: Debits ({$totalDebit}) != Credits ({$totalCredit})");
        }

        // 3. Atomically lock and increment sequence
        $this->pdo->beginTransaction();
        try {
            $driver = $this->pdo->getAttribute(PDO::ATTR_DRIVER_NAME);
            $lockClause = ($driver === 'mysql') ? ' FOR UPDATE' : '';
            $seqStmt = $this->pdo->prepare("SELECT current_value, prefix FROM consecutive_sequences WHERE company_id = ? AND voucher_type = ?" . $lockClause);
            $seqStmt->execute([$companyId, $voucherType]);
            $seq = $seqStmt->fetch();
            if (!$seq) {
                throw new RuntimeException("No sequence configured for voucher type.");
            }
            
            $nextVal = ((int)$seq['current_value']) + 1;
            $consecutive = sprintf("%s-%s-%04d", $seq['prefix'], substr($period, 0, 4), $nextVal);

            $updSeq = $this->pdo->prepare("UPDATE consecutive_sequences SET current_value = ? WHERE company_id = ? AND voucher_type = ?");
            $updSeq->execute([$nextVal, $companyId, $voucherType]);

            $voucherId = bin2hex(random_bytes(16));
            $insVoucher = $this->pdo->prepare("INSERT INTO vouchers (id, company_id, consecutive, voucher_type, transaction_date, period, status, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, 'CONTABILIZADO', ?, ?)");
            $insVoucher->execute([$voucherId, $companyId, $consecutive, $voucherType, $date, $period, $notes, $userId]);

            $insLine = $this->pdo->prepare("INSERT INTO voucher_lines (id, voucher_id, account_code, third_party_nit, third_party_name, concept, base_amount, debit, credit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
            foreach ($lines as $line) {
                $lineId = bin2hex(random_bytes(16));
                $insLine->execute([
                    $lineId,
                    $voucherId,
                    $line['account_code'],
                    $line['third_party_nit'],
                    $line['third_party_name'],
                    $line['concept'],
                    $line['base_amount'] ?? 0,
                    $line['debit'] ?? 0,
                    $line['credit'] ?? 0
                ]);
            }

            $this->pdo->commit();
            return $consecutive;
        } catch (\Throwable $e) {
            $this->pdo->rollBack();
            throw $e;
        }
    }
}