<?php
/**
 * Idempotent Database Migration Script v2: Products & Pricing Audit Trail
 */
$dsn = getenv('DB_DSN') ?: 'sqlite:' . __DIR__ . '/database.sqlite';
$pdo = new PDO($dsn, getenv('DB_USER') ?: null, getenv('DB_PASS') ?: null, [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
]);

echo "[MIGRATION] Starting Database Migration v2...\n";

try {
    $pdo->beginTransaction();

    $isSqlite = strpos($dsn, 'sqlite') !== false;

    if ($isSqlite) {
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Abarrotes',
                price REAL NOT NULL DEFAULT 0,
                cost REAL NOT NULL DEFAULT 0,
                stock INTEGER NOT NULL DEFAULT 0,
                min_stock INTEGER NOT NULL DEFAULT 5,
                iva_rate REAL NOT NULL DEFAULT 0.19,
                barcode TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS product_pricing_history (
                id TEXT PRIMARY KEY,
                product_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                old_price REAL NOT NULL,
                new_price REAL NOT NULL,
                old_cost REAL NOT NULL,
                new_cost REAL NOT NULL,
                old_iva_rate REAL NOT NULL,
                new_iva_rate REAL NOT NULL,
                changed_by TEXT NOT NULL,
                changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                reason TEXT NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            );
        ");
    } else {
        $sql = file_get_contents(__DIR__ . '/schema.sql');
        $pdo->exec($sql);
    }

    $pdo->commit();
    echo "[MIGRATION] SUCCESS: Migration v2 applied cleanly.\n";
} catch (Exception $e) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }
    echo "[MIGRATION] FAILED: " . $e->getMessage() . "\n";
    exit(1);
}
