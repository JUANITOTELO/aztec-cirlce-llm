<?php

declare(strict_types=1);

namespace App\Controllers;

use App\Services\LedgerService;
use PDOException;

class TransactionController
{
    public function __construct(private LedgerService $ledgerService)
    {}

    public function sync(array $request): void
    {
        // Input validation would be handled by a middleware in a full app
        $transactionData = $request['body'];

        try {
            $result = $this->ledgerService->postJournalEntry($transactionData);
            http_response_code(201);
            echo json_encode(['status' => 'success', 'transaction_id' => $result]);
        } catch (PDOException $e) {
            // Check for unique constraint violation (idempotency)
            if ($e->errorInfo[1] == 1062) { 
                http_response_code(409);
                echo json_encode([
                    'error' => 'Conflict: Transaction already exists.',
                    'client_transaction_id' => $transactionData['client_transaction_id']
                ]);
            } else {
                // Re-throw for generic error handler
                throw $e;
            }
        } catch (\InvalidArgumentException $e) {
            http_response_code(400);
            echo json_encode(['error' => $e->getMessage()]);
        }
    }
}
