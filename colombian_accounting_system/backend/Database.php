<?php
declare(strict_types=1);

namespace Sifco\Database;

use PDO;
use PDOException;
use RuntimeException;

class Database {
    private static ?PDO $instance = null;

    public static function getConnection(): PDO {
        if (self::$instance === null) {
            $driver = getenv('DB_DRIVER') ?: 'sqlite';

            if ($driver === 'mysql') {
                $host = getenv('DB_HOST') ?: '127.0.0.1';
                $port = getenv('DB_PORT') ?: '3306';
                $dbname = getenv('DB_NAME') ?: 'sifco_contable';
                $user = getenv('DB_USER') ?: 'root';
                $pass = getenv('DB_PASS') ?: '';

                $dsn = "mysql:host={$host};port={$port};dbname={$dbname};charset=utf8mb4";
                $options = [
                    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                    PDO::ATTR_EMULATE_PREPARES => false,
                ];

                try {
                    self::$instance = new PDO($dsn, $user, $pass, $options);
                } catch (PDOException $e) {
                    throw new RuntimeException("MySQL connection failed: " . $e->getMessage());
                }
            } else {
                // SQLite (Zero-config local development and testing)
                $dbPath = getenv('DB_PATH') ?: __DIR__ . '/sifco_contable.sqlite';
                $isNew = !file_exists($dbPath);
                
                try {
                    self::$instance = new PDO("sqlite:" . $dbPath);
                    self::$instance->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
                    self::$instance->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
                    self::$instance->exec("PRAGMA foreign_keys = ON;");

                    if ($isNew) {
                        self::initializeSchema(self::$instance);
                    }
                } catch (PDOException $e) {
                    throw new RuntimeException("SQLite connection failed: " . $e->getMessage());
                }
            }
        }
        return self::$instance;
    }

    public static function resetInstance(): void {
        self::$instance = null;
    }

    public static function initializeSchema(PDO $pdo): void {
        $schema = <<<SQL
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            nit TEXT NOT NULL UNIQUE,
            dv TEXT NOT NULL,
            business_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS accounting_periods (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            period TEXT NOT NULL,
            is_closed INTEGER NOT NULL DEFAULT 0,
            closed_at DATETIME NULL,
            closed_by TEXT NULL,
            UNIQUE(company_id, period),
            FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS consecutive_sequences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT NOT NULL,
            voucher_type TEXT NOT NULL,
            current_value INTEGER NOT NULL DEFAULT 0,
            prefix TEXT NOT NULL,
            UNIQUE(company_id, voucher_type),
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );

        CREATE TABLE IF NOT EXISTS vouchers (
            id TEXT PRIMARY KEY,
            company_id TEXT NOT NULL,
            consecutive TEXT NOT NULL,
            voucher_type TEXT NOT NULL,
            transaction_date TEXT NOT NULL,
            period TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'BORRADOR',
            notes TEXT NULL,
            created_by TEXT NOT NULL,
            approved_by TEXT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id)
        );

        CREATE TABLE IF NOT EXISTS voucher_lines (
            id TEXT PRIMARY KEY,
            voucher_id TEXT NOT NULL,
            account_code TEXT NOT NULL,
            third_party_nit TEXT NOT NULL,
            third_party_name TEXT NOT NULL,
            concept TEXT NOT NULL,
            base_amount REAL NOT NULL DEFAULT 0.0,
            debit REAL NOT NULL DEFAULT 0.0,
            credit REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (voucher_id) REFERENCES vouchers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS puc_accounts (
            code TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            nature TEXT NOT NULL, -- DEBITO | CREDITO
            level INTEGER NOT NULL,
            requires_third_party INTEGER NOT NULL DEFAULT 1
        );

        -- Seeds initial company and sequences
        INSERT OR IGNORE INTO companies (id, nit, dv, business_name) 
        VALUES ('comp-001', '901.458.789', '4', 'Inversiones y Soluciones Andinas SAS');

        INSERT OR IGNORE INTO consecutive_sequences (company_id, voucher_type, current_value, prefix)
        VALUES 
            ('comp-001', 'FACTURA_VENTA', 0, 'FV'),
            ('comp-001', 'COMPROBANTE_EGRESO', 0, 'CE'),
            ('comp-001', 'RECIBO_CAJA', 0, 'RC'),
            ('comp-001', 'NOTA_CONTABLE', 0, 'NC');

        INSERT OR IGNORE INTO accounting_periods (id, company_id, period, is_closed)
        VALUES 
            ('per-001', 'comp-001', '2025-01', 1),
            ('per-002', 'comp-001', '2025-02', 0);

        -- PUC Colombia standard accounts
        INSERT OR IGNORE INTO puc_accounts (code, name, nature, level) VALUES
            ('110505', 'Caja General', 'DEBITO', 3),
            ('111005', 'Bancos Nacionales (Bancolombia)', 'DEBITO', 3),
            ('130505', 'Clientes Nacionales', 'DEBITO', 3),
            ('135515', 'Anticipo Retención en la Fuente 2.5%', 'DEBITO', 3),
            ('135518', 'Anticipo ReteICA', 'DEBITO', 3),
            ('143505', 'Mercancías no fabricadas por la empresa', 'DEBITO', 3),
            ('220505', 'Proveedores Nacionales', 'CREDITO', 3),
            ('236540', 'Retención en la Fuente por Pagar (Compras 2.5%)', 'CREDITO', 3),
            ('236801', 'Impuesto de Industria y Comercio Retenido (ReteICA)', 'CREDITO', 3),
            ('240801', 'Impuesto sobre las Ventas por Pagar (IVA Generado 19%)', 'CREDITO', 3),
            ('310505', 'Capital Suscrito y Pagado', 'CREDITO', 3),
            ('413505', 'Comercio al por Mayor y al por Menor', 'CREDITO', 3),
            ('510506', 'Sueldos de Personal Administrativo', 'DEBITO', 3),
            ('613505', 'Costo de Ventas Comercio', 'DEBITO', 3);
SQL;
        $pdo->exec($schema);
    }
}