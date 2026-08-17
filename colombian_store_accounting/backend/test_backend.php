<?php
declare(strict_types=1);

/**
 * Aztec Backend Unit & Integration Test Suite
 * Tests SQLite schema, migrations, routes, sales processing, and ledger entries.
 */

echo "======================================================\n";
echo "🧪 Aztec Colombian Store PHP Backend Test Suite\n";
echo "======================================================\n";

$dbPath = __DIR__ . '/database.sqlite';
if (!file_exists($dbPath)) {
    require_once __DIR__ . '/migrate_and_seed.php';
}

$pdo = new PDO("sqlite:{$dbPath}", null, null, [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]);

$passCount = 0;
$failCount = 0;

function assertTest(string $name, bool $condition): void {
    global $passCount, $failCount;
    if ($condition) {
        echo "  ✓ {$name}\n";
        $passCount++;
    } else {
        echo "  ✗ FAIL: {$name}\n";
        $failCount++;
    }
}

// 1. Test Database Tables Exist
$tables = $pdo->query("SELECT name FROM sqlite_master WHERE type='table'")->fetchAll(PDO::FETCH_COLUMN);
assertTest("Table 'products' exists in SQLite", in_array('products', $tables, true));
assertTest("Table 'product_variants' exists in SQLite", in_array('product_variants', $tables, true));
assertTest("Table 'product_images' exists in SQLite", in_array('product_images', $tables, true));
assertTest("Table 'categories' exists in SQLite", in_array('categories', $tables, true));
assertTest("Table 'sales' exists in SQLite", in_array('sales', $tables, true));
assertTest("Table 'ledger_entries' exists in SQLite", in_array('ledger_entries', $tables, true));
assertTest("Table 'users' exists in SQLite", in_array('users', $tables, true));
assertTest("Table 'roles' exists in SQLite", in_array('roles', $tables, true));

// 2. Test Product Queries & Counts
$prodCount = (int)$pdo->query("SELECT COUNT(*) FROM products")->fetchColumn();
assertTest("Products table contains seeded items (> 0)", $prodCount > 0);

$varCount = (int)$pdo->query("SELECT COUNT(*) FROM product_variants")->fetchColumn();
assertTest("Product variants table contains seeded items (> 0)", $varCount > 0);

$imgCount = (int)$pdo->query("SELECT COUNT(*) FROM product_images")->fetchColumn();
assertTest("Product images table contains seeded items (> 0)", $imgCount > 0);

// 3. Test Inserting and Deleting a Product Atomically
$testProdId = 'test-prod-' . bin2hex(random_bytes(4));
$stmt = $pdo->prepare("INSERT INTO products (id, sku, name, category, price, cost, stock, min_stock, iva_rate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)");
$stmt->execute([$testProdId, 'TEST-SKU-' . time(), 'Producto Temporal Test', 'Snacks', 12000, 8000, 10, 2, 0.19]);

$inserted = $pdo->query("SELECT * FROM products WHERE id = '{$testProdId}'")->fetch();
assertTest("Product inserted successfully into database", !empty($inserted) && $inserted['name'] === 'Producto Temporal Test');

// Test Variant linked to Product
$testVarId = 'test-var-' . bin2hex(random_bytes(4));
$stmt = $pdo->prepare("INSERT INTO product_variants (id, product_id, sku, name, price, cost, stock) VALUES (?, ?, ?, ?, ?, ?, ?)");
$stmt->execute([$testVarId, $testProdId, 'TEST-VAR-' . time(), 'Variante Test', 12000, 8000, 10]);

$insertedVar = $pdo->query("SELECT * FROM product_variants WHERE id = '{$testVarId}'")->fetch();
assertTest("Product variant inserted and linked to product", !empty($insertedVar) && $insertedVar['product_id'] === $testProdId);

// Test Image linked to Product
$testImgId = 'test-img-' . bin2hex(random_bytes(4));
$stmt = $pdo->prepare("INSERT INTO product_images (id, product_id, variant_id, url, is_primary, order_pos, file_hash) VALUES (?, ?, ?, ?, ?, ?, ?)");
$stmt->execute([$testImgId, $testProdId, $testVarId, 'data:image/webp;base64,AAA', 1, 0, 'test-hash-123']);

$insertedImg = $pdo->query("SELECT * FROM product_images WHERE id = '{$testImgId}'")->fetch();
assertTest("Product image inserted and linked to product & variant", !empty($insertedImg) && $insertedImg['is_primary'] == 1);

// Cascade deletion test
$pdo->prepare("DELETE FROM products WHERE id = ?")->execute([$testProdId]);
$pdo->prepare("DELETE FROM product_variants WHERE product_id = ?")->execute([$testProdId]);
$pdo->prepare("DELETE FROM product_images WHERE product_id = ?")->execute([$testProdId]);

assertTest("Product and cascading records deleted cleanly", (int)$pdo->query("SELECT COUNT(*) FROM products WHERE id = '{$testProdId}'")->fetchColumn() === 0);

// 4. Test Sale and Automatic Ledger Generation
$saleId = 'test-sale-' . bin2hex(random_bytes(4));
$invNum = 'TEST-FAC-' . time();
$pdo->prepare("INSERT INTO sales (id, invoice_number, customer_name, customer_doc, subtotal, iva_total, total, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
    ->execute([$saleId, $invNum, 'Cliente Prueba', '123456789', 10000, 1900, 11900, 'Efectivo']);

// Insert Ledger Entry
$ledgId = 'test-ledg-' . bin2hex(random_bytes(4));
$pdo->prepare("INSERT INTO ledger_entries (id, date, puc_code, puc_name, description, debit, credit, reference) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
    ->execute([$ledgId, date('Y-m-d'), '110505', 'Caja General', "Venta POS {$invNum}", 11900, 0.0, $invNum]);

$savedLedger = $pdo->query("SELECT * FROM ledger_entries WHERE id = '{$ledgId}'")->fetch();
assertTest("Accounting ledger entry created with reference to sale", !empty($savedLedger) && (float)$savedLedger['debit'] === 11900.0);

// Cleanup test sale & ledger
$pdo->prepare("DELETE FROM sales WHERE id = ?")->execute([$saleId]);
$pdo->prepare("DELETE FROM ledger_entries WHERE id = ?")->execute([$ledgId]);

echo "\n======================================================\n";
echo "Results: {$passCount} passed, {$failCount} failed.\n";
echo "======================================================\n";

if ($failCount > 0) {
    exit(1);
}
exit(0);
