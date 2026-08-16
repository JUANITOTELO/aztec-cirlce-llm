<?php

declare(strict_types=1);

namespace App\Services;

use PDO;
use InvalidArgumentException;

class LedgerService
{
    private PDO $db;

    public function __construct(DatabaseService $dbService)
    {
        $this->db = $dbService->getConnection();
    }

    /**
     * Posts a journal entry within a SERIALIZABLE transaction.
     * Enforces double-entry bookkeeping rules.
     */
    public function postJournalEntry(array $data): int
    {
        $this->validateJournalEntry($data);

        $this->db->beginTransaction();

        try {
            // 1. Insert the main transaction record
            $stmt = $this->db->prepare(
                'INSERT INTO transactions (client_transaction_id, user_id, puc_version_id, transaction_date, description) VALUES (?, ?, ?, ?, ?)'
            );
            $stmt->execute([
                $data['client_transaction_id'],
                $data['user_id'],
                $data['puc_version_id'],
                $data['transaction_date'],
                $data['description']
            ]);
            $transactionId = (int)$this->db->lastInsertId();

            // 2. Insert ledger entries
            $entryStmt = $this->db->prepare(
                'INSERT INTO ledger_entries (transaction_id, account_code, debit, credit) VALUES (?, ?, ?, ?)'
            );
            foreach ($data['entries'] as $entry) {
                $entryStmt->execute([
                    $transactionId,
                    $entry['account_code'],
                    $entry['debit'] ?? '0.00',
                    $entry['credit'] ?? '0.00'
                ]);
            }
            
            // 3. (Optional) Update account balances using pessimistic locking
            // This would involve a separate `account_balances` table.
            // Example: SELECT balance FROM account_balances WHERE account_code = ? FOR UPDATE;

            $this->db->commit();
            return $transactionId;
        } catch (\Exception $e) {
            $this->db->rollBack();
            throw $e; // Re-throw to be handled by the controller
        }
    }

    private function validateJournalEntry(array $data): void
    {
        if (empty($data['entries']) || !is_array($data['entries'])) {
            throw new InvalidArgumentException('Transaction must have at least one entry.');
        }

        $totalDebit = 0.00;
        $totalCredit = 0.00;

        foreach ($data['entries'] as $entry) {
            $debit = (float)($entry['debit'] ?? 0.00);
            $credit = (float)($entry['credit'] ?? 0.00);
            if ($debit < 0 || $credit < 0) {
                throw new InvalidArgumentException('Debit and credit values cannot be negative.');
            }
            $totalDebit += $debit;
            $totalCredit += $credit;
        }

        // Use a small epsilon for float comparison
        if (abs($totalDebit - $totalCredit) > 0.001) {
            throw new InvalidArgumentException('Debits do not equal credits.');
        }
    }
}
