<?php
declare(strict_types=1);

require_once __DIR__ . '/Database.php';
require_once __DIR__ . '/VoucherService.php';

use Sifco\Database\Database;
use Sifco\Services\VoucherService;

// Enable CORS
header("Access-Control-Allow-Origin: *");
header("Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS");
header("Access-Control-Allow-Headers: Content-Type, Authorization");

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

header("Content-Type: application/json; charset=UTF-8");

$pdo = Database::getConnection();
$service = new VoucherService($pdo);

$uri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'];

// Helper to send json
function sendJson(int $code, array $data): void {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

try {
    // Health / Status
    if ($uri === '/api/status' || $uri === '/status') {
        $driver = $pdo->getAttribute(PDO::ATTR_DRIVER_NAME);
        sendJson(200, [
            'status' => 'online',
            'system' => 'SIFCO Contable Colombiano',
            'version' => '1.0.0',
            'database_driver' => $driver,
            'dian_resolution' => 'Resolución DIAN 18764000001 (Vigente)',
            'timestamp' => date('c')
        ]);
    }

    // PUC Accounts List
    if ($uri === '/api/puc' && $method === 'GET') {
        $stmt = $pdo->query("SELECT * FROM puc_accounts ORDER BY code ASC");
        $accounts = $stmt->fetchAll();
        sendJson(200, ['puc_accounts' => $accounts]);
    }

    // List Vouchers
    if ($uri === '/api/vouchers' && $method === 'GET') {
        $stmt = $pdo->query("SELECT * FROM vouchers ORDER BY transaction_date DESC, consecutive DESC");
        $vouchers = $stmt->fetchAll();
        
        $lineStmt = $pdo->prepare("SELECT * FROM voucher_lines WHERE voucher_id = ?");
        foreach ($vouchers as &$v) {
            $lineStmt->execute([$v['id']]);
            $v['lines'] = $lineStmt->fetchAll();
        }
        sendJson(200, ['vouchers' => $vouchers]);
    }

    // Create Voucher (Double Entry Validated)
    if ($uri === '/api/vouchers' && $method === 'POST') {
        $body = json_decode(file_get_contents('php://input'), true);
        if (!$body) {
            sendJson(400, ['error' => 'Invalid JSON body']);
        }

        $companyId = $body['company_id'] ?? 'comp-001';
        $voucherType = $body['voucher_type'] ?? 'FACTURA_VENTA';
        $date = $body['date'] ?? date('Y-m-d');
        $notes = $body['notes'] ?? 'Comprobante generado';
        $lines = $body['lines'] ?? [];
        $userId = $body['user_id'] ?? 'USR-ADMIN';

        $consecutive = $service->createVoucher($companyId, $voucherType, $date, $notes, $lines, $userId);
        sendJson(201, [
            'success' => true,
            'consecutive' => $consecutive,
            'message' => "Comprobante {$consecutive} contabilizado con éxito bajo partida doble."
        ]);
    }

    // Settle DIAN Taxes
    if ($uri === '/api/taxes/settle' && $method === 'POST') {
        $body = json_decode(file_get_contents('php://input'), true) ?? [];
        $subtotal = (float)($body['subtotal'] ?? 0);
        $ivaRate = (float)($body['iva_rate'] ?? 19.0);
        $reteFuenteRate = (float)($body['rete_fuente_rate'] ?? 2.5);
        $reteIcaPermil = (float)($body['rete_ica_permil'] ?? 9.66);
        $applyReteIva = (bool)($body['apply_rete_iva'] ?? false);

        $ivaAmount = round($subtotal * ($ivaRate / 100.0), 2);
        $reteFuenteAmount = round($subtotal * ($reteFuenteRate / 100.0), 2);
        $reteIcaAmount = round($subtotal * ($reteIcaPermil / 1000.0), 2);
        $reteIvaAmount = $applyReteIva ? round($ivaAmount * 0.15, 2) : 0.0;

        $totalPayable = round($subtotal + $ivaAmount - $reteFuenteAmount - $reteIcaAmount - $reteIvaAmount, 2);

        sendJson(200, [
            'subtotal' => $subtotal,
            'iva_amount' => $ivaAmount,
            'rete_fuente_amount' => $reteFuenteAmount,
            'rete_ica_amount' => $reteIcaAmount,
            'rete_iva_amount' => $reteIvaAmount,
            'total_payable' => $totalPayable,
            'total_debits' => round($totalPayable + $reteFuenteAmount + $reteIcaAmount + $reteIvaAmount, 2),
            'total_credits' => round($subtotal + $ivaAmount, 2),
        ]);
    }

    // Trial Balance Report
    if (str_starts_with($uri, '/api/reports/trial-balance') && $method === 'GET') {
        $period = $_GET['period'] ?? date('Y-m');
        $stmt = $pdo->prepare("
            SELECT 
                SUBSTR(vl.account_code, 1, 1) as class_code,
                vl.account_code,
                SUM(vl.debit) as total_debit,
                SUM(vl.credit) as total_credit
            FROM vouchers v
            JOIN voucher_lines vl ON v.id = vl.voucher_id
            WHERE v.period = ? AND v.status = 'CONTABILIZADO'
            GROUP BY vl.account_code
            ORDER BY vl.account_code ASC
        ");
        $stmt->execute([$period]);
        $rows = $stmt->fetchAll();

        $sumDebits = 0;
        $sumCredits = 0;
        foreach ($rows as $r) {
            $sumDebits += (float)$r['total_debit'];
            $sumCredits += (float)$r['total_credit'];
        }

        sendJson(200, [
            'period' => $period,
            'rows' => $rows,
            'sum_debits' => round($sumDebits, 2),
            'sum_credits' => round($sumCredits, 2),
            'is_balanced' => abs($sumDebits - $sumCredits) < 0.01
        ]);
    }

    // 404
    sendJson(404, ['error' => 'Endpoint not found', 'path' => $uri]);

} catch (\Throwable $e) {
    sendJson(500, [
        'error' => 'Internal Server Error',
        'message' => $e->getMessage()
    ]);
}
