<?php
/**
 * Database Migration & RBAC Access Seeder
 * Sets up tables and assigns all feature access (including user & role management) to role-admin
 */
declare(strict_types=1);

$host = getenv('DB_HOST') ?: '127.0.0.1';
$port = getenv('DB_PORT') ?: '3306';
$dbname = getenv('DB_DATABASE') ?: 'aztec_db';
$user = getenv('DB_USERNAME') ?: 'root';
$password = getenv('DB_PASSWORD') ?: '';
$driver = getenv('DB_CONNECTION') ?: 'sqlite';

try {
    if ($driver === 'mysql') {
        $pdo = new PDO("mysql:host={$host};port={$port};dbname={$dbname};charset=utf8mb4", $user, $password, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
    } else {
        $dbPath = __DIR__ . '/aztec.sqlite';
        $pdo = new PDO("sqlite:{$dbPath}", null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
    }

    echo "[INFO] Connected to database successfully ({$driver}).\n";

    // 1. Create tables
    $pdo->exec("
        CREATE TABLE IF NOT EXISTS roles (
            id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            is_system INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS permissions (
            id VARCHAR(64) PRIMARY KEY,
            module VARCHAR(50) NOT NULL,
            feature_key VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(255) NOT NULL
        );

        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id VARCHAR(64) NOT NULL,
            permission_id VARCHAR(64) NOT NULL,
            PRIMARY KEY (role_id, permission_id)
        );

        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(64) PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role_id VARCHAR(64) NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ");

    // 2. Insert or update Admin Role
    $stmt = $pdo->prepare("
        INSERT INTO roles (id, name, description, is_system)
        VALUES ('role-admin', 'Admin', 'Acceso total y configuración de usuarios, roles y módulos del sistema', 1)
        ON CONFLICT(id) DO UPDATE SET 
            description = excluded.description,
            is_system = 1;
    ");
    try {
        $stmt->execute();
    } catch (PDOException $e) {
        // Fallback for MySQL duplicate key
        $pdo->exec("
            INSERT INTO roles (id, name, description, is_system)
            VALUES ('role-admin', 'Admin', 'Acceso total y configuración de usuarios, roles y módulos del sistema', 1)
            ON DUPLICATE KEY UPDATE description = VALUES(description), is_system = 1;
        ");
    }

    // 3. Define permissions including user & access configuration features
    $features = [
        ['perm-pos-all', 'pos', 'pos.access', 'Acceso completo al módulo Punto de Venta POS'],
        ['perm-inv-all', 'inventory', 'inventory.manage', 'Gestión de productos y existencias'],
        ['perm-led-all', 'ledger', 'ledger.manage', 'Libro diario y mayor contable'],
        ['perm-dian-all', 'dian', 'dian.manage', 'Liquidación tributaria DIAN'],
        ['perm-puc-all', 'puc', 'puc.manage', 'Catálogo de cuentas PUC'],
        ['perm-usr-view', 'users', 'users.view', 'Ver lista de usuarios y roles'],
        ['perm-usr-manage', 'users', 'users.manage', 'Crear, editar, eliminar y configurar usuarios'],
        ['perm-role-config', 'users', 'roles.configure_access', 'Configurar roles y matriz de accesos']
    ];

    foreach ($features as [$id, $module, $key, $desc]) {
        try {
            $permStmt = $pdo->prepare("
                INSERT INTO permissions (id, module, feature_key, description)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET module = excluded.module, description = excluded.description;
            ");
            $permStmt->execute([$id, $module, $key, $desc]);
        } catch (PDOException $e) {
            $permStmt = $pdo->prepare("
                INSERT INTO permissions (id, module, feature_key, description)
                VALUES (?, ?, ?, ?)
                ON DUPLICATE KEY UPDATE module = VALUES(module), description = VALUES(description);
            ");
            $permStmt->execute([$id, $module, $key, $desc]);
        }
    }

    // 4. Assign all permissions to role-admin
    $assignStmt = $pdo->prepare("
        INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
        SELECT 'role-admin', id FROM permissions;
    ");
    try {
        $assignStmt->execute();
    } catch (PDOException $e) {
        $pdo->exec("INSERT IGNORE INTO role_permissions (role_id, permission_id) SELECT 'role-admin', id FROM permissions;");
    }

    echo "[SUCCESS] Admin role granted full feature access & user/permission configuration in database.\n";
} catch (Exception $ex) {
    fwrite(STDERR, "[ERROR] Database initialization failed: " . $ex->getMessage() . "\n");
    exit(1);
}
