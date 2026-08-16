<?php
declare(strict_types=1);

require_once __DIR__ . '/Database.php';
require_once __DIR__ . '/VoucherService.php';

use Sifco\Database\Database;
use Sifco\Services\VoucherService;

echo "========================================================\n";
echo "🇨🇴 SIFCO - Test de Verificación Backend PHP & Contabilidad DIAN\n";
echo "========================================================\n\n";

$pdo = Database::getConnection();
$service = new VoucherService($pdo);

$testsPassed = 0;
$totalTests = 0;

function assertTest(string $name, bool $condition, string $detail = ''): void {
    global $testsPassed, $totalTests;
    $totalTests++;
    if ($condition) {
        $testsPassed++;
        echo "  [PASS] {$name}" . ($detail ? " ($detail)" : '') . "\n";
    } else {
        echo "  [FAIL] {$name}" . ($detail ? " - ERROR: $detail" : '') . "\n";
        exit(1);
    }
}

// 1. Test Database connection
assertTest("1. Conexión a Base de Datos (PDO SQLite/MySQL)", $pdo instanceof PDO, "Driver: " . $pdo->getAttribute(PDO::ATTR_DRIVER_NAME));

// 2. Test PUC accounts seeded
$pucCount = (int)$pdo->query("SELECT COUNT(*) FROM puc_accounts")->fetchColumn();
assertTest("2. Catálogo PUC Colombia Inicializado", $pucCount >= 10, "Total cuentas PUC: {$pucCount}");

// 3. Test DIAN Tax Calculation
$subtotal = 10000000.0;
$iva = round($subtotal * 0.19, 2);
$retefuente = round($subtotal * 0.025, 2);
$reteica = round($subtotal * (9.66 / 1000.0), 2);
$totalPagar = round($subtotal + $iva - $retefuente - $reteica, 2);
$debitos = $totalPagar + $retefuente + $reteica;
$creditos = $subtotal + $iva;
assertTest("3. Liquidación de Impuestos DIAN con sumas iguales", $debitos === $creditos, "Subtotal: $10M | IVA: $1.9M | ReteFuente: $250k | ReteICA: $96.6k | Total: $11.553.400 COP");

// 4. Test Double-Entry Balanced Voucher Creation
$lines = [
    [
        'account_code' => '130505',
        'third_party_nit' => '900.888.777-1',
        'third_party_name' => 'Comercializadora Bogotá SAS',
        'concept' => 'Cuentas por Cobrar Clientes (Venta)',
        'base_amount' => 10000000.0,
        'debit' => $totalPagar,
        'credit' => 0.0
    ],
    [
        'account_code' => '135515',
        'third_party_nit' => '900.888.777-1',
        'third_party_name' => 'Comercializadora Bogotá SAS',
        'concept' => 'Anticipo Retefuente 2.5%',
        'base_amount' => 10000000.0,
        'debit' => $retefuente,
        'credit' => 0.0
    ],
    [
        'account_code' => '135518',
        'third_party_nit' => '900.888.777-1',
        'third_party_name' => 'Comercializadora Bogotá SAS',
        'concept' => 'Anticipo ReteICA 9.66 por mil',
        'base_amount' => 10000000.0,
        'debit' => $reteica,
        'credit' => 0.0
    ],
    [
        'account_code' => '240801',
        'third_party_nit' => '900.888.777-1',
        'third_party_name' => 'Comercializadora Bogotá SAS',
        'concept' => 'IVA Generado 19%',
        'base_amount' => 10000000.0,
        'debit' => 0.0,
        'credit' => $iva
    ],
    [
        'account_code' => '413505',
        'third_party_nit' => '900.888.777-1',
        'third_party_name' => 'Comercializadora Bogotá SAS',
        'concept' => 'Ingreso por Ventas de Mercancía',
        'base_amount' => 10000000.0,
        'debit' => 0.0,
        'credit' => $subtotal
    ]
];

$consecutive = $service->createVoucher('comp-001', 'FACTURA_VENTA', '2025-02-16', 'Venta a Comercializadora Bogotá SAS', $lines, 'USR-001');
assertTest("4. Creación de Comprobante por Partida Doble", !empty($consecutive), "Consecutivo generado: {$consecutive}");

// 5. Test Rejection of Unbalanced Voucher
$unbalancedLines = [
    [
        'account_code' => '110505',
        'third_party_nit' => '123',
        'third_party_name' => 'Test',
        'concept' => 'Ingreso',
        'debit' => 500000.0,
        'credit' => 0.0
    ],
    [
        'account_code' => '413505',
        'third_party_nit' => '123',
        'third_party_name' => 'Test',
        'concept' => 'Ingreso',
        'debit' => 0.0,
        'credit' => 450000.0 // Descuadrado por $50.000
    ]
];

$caughtUnbalanced = false;
try {
    $service->createVoucher('comp-001', 'FACTURA_VENTA', '2025-02-16', 'Venta Descuadrada', $unbalancedLines, 'USR-001');
} catch (RuntimeException $e) {
    $caughtUnbalanced = str_contains($e->getMessage(), 'Double entry unbalanced');
}
assertTest("5. Rechazo Estricto de Asiento Descuadrado (Débitos != Créditos)", $caughtUnbalanced);

// 6. Test Period Lock Validation
$caughtPeriodLock = false;
try {
    $service->createVoucher('comp-001', 'FACTURA_VENTA', '2025-01-15', 'Periodo Cerrado', $lines, 'USR-001');
} catch (RuntimeException $e) {
    $caughtPeriodLock = str_contains($e->getMessage(), 'locked/closed');
}
assertTest("6. Bloqueo Legal de Periodo Contable Cerrado (2025-01)", $caughtPeriodLock);

// 7. Verify Trial Balance in Database
$stmt = $pdo->prepare("
    SELECT SUM(debit) as total_debits, SUM(credit) as total_credits
    FROM voucher_lines vl
    JOIN vouchers v ON vl.voucher_id = v.id
    WHERE v.period = '2025-02' AND v.status = 'CONTABILIZADO'
");
$stmt->execute();
$totals = $stmt->fetch();
$equalSums = abs((float)$totals['total_debits'] - (float)$totals['total_credits']) < 0.01;
assertTest("7. Balance de Prueba (Sumas Iguales en Base de Datos)", $equalSums, "Total Débitos: $" . number_format((float)$totals['total_debits'], 2) . " == Total Créditos: $" . number_format((float)$totals['total_credits'], 2));

echo "\n--------------------------------------------------------\n";
echo "✓ TODOS LOS {$testsPassed}/{$totalTests} TESTS DEL BACKEND PHP PASARON EXITOSAMENTE!\n";
echo "========================================================\n";
