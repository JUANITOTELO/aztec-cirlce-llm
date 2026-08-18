<?php
declare(strict_types=1);

/**
 * Aztec Colombian Store & Accounting Migration & Seed Engine
 */

$dbPath = __DIR__ . '/database.sqlite';
$schemaPath = __DIR__ . '/schema.sql';

echo "[BACKEND MIGRATION] Connecting to SQLite: {$dbPath}...\n";

$pdo = new PDO("sqlite:{$dbPath}", null, null, [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
]);

// Apply schema
$schemaSql = file_get_contents($schemaPath);
$pdo->exec($schemaSql);

// Column check for products.image
$cols = $pdo->query("PRAGMA table_info(products)")->fetchAll();
$hasImage = false;
foreach ($cols as $col) {
    if ($col['name'] === 'image') $hasImage = true;
}
if (!$hasImage) {
    $pdo->exec("ALTER TABLE products ADD COLUMN image TEXT");
}

echo "[BACKEND MIGRATION] Schema executed successfully.\n";

// Seed Categories if empty
$catCount = (int)$pdo->query("SELECT COUNT(*) FROM categories")->fetchColumn();
if ($catCount === 0) {
    echo "[BACKEND SEED] Seeding Categories...\n";
    $cats = [
        ['cat-1', 'Abarrotes', 'Granos, aceites, pastas y víveres', '#3B82F6'],
        ['cat-2', 'Bebidas', 'Jugos, gaseosas, aguas y café', '#10B981'],
        ['cat-3', 'Lácteos', 'Leches, quesos, yogures y derivados', '#8B5CF6'],
        ['cat-4', 'Aseo', 'Jabones, detergentes y desinfectantes', '#EC4899'],
        ['cat-5', 'Snacks', 'Papas, galletas, chocolates y confitería', '#F59E0B'],
    ];
    $stmt = $pdo->prepare("INSERT INTO categories (id, name, description, color) VALUES (?, ?, ?, ?)");
    foreach ($cats as $c) {
        $stmt->execute($c);
    }
}

// Seed Roles if empty
$roleCount = (int)$pdo->query("SELECT COUNT(*) FROM roles")->fetchColumn();
if ($roleCount === 0) {
    echo "[BACKEND SEED] Seeding Roles...\n";
    $roles = [
        ['role-admin', 'Administrador', 'Control total del sistema contable y POS', json_encode(['pos', 'products', 'inventory', 'ledger', 'dian', 'puc', 'users']), 1],
        ['role-contador', 'Contador', 'Acceso a libro diario, reportes DIAN y catálogo', json_encode(['products', 'ledger', 'dian', 'puc', 'inventory']), 1],
        ['role-cajero', 'Cajero', 'Operación de caja y registro de ventas', json_encode(['pos']), 1],
    ];
    $stmt = $pdo->prepare("INSERT INTO roles (id, name, description, modules, is_system) VALUES (?, ?, ?, ?, ?)");
    foreach ($roles as $r) {
        $stmt->execute($r);
    }
}

// Seed Users if empty
$userCount = (int)$pdo->query("SELECT COUNT(*) FROM users")->fetchColumn();
if ($userCount === 0) {
    echo "[BACKEND SEED] Seeding Users...\n";
    $users = [
        ['usr-admin', 'Administrador General', 'admin@aztec.co', 'role-admin', 'admin', json_encode(['*']), 1],
        ['usr-cajero', 'Carlos Cajero', 'cajero@aztec.co', 'role-cajero', 'cajero', json_encode(['pos.sell']), 1],
        ['usr-contador', 'Diana Contadora', 'contador@aztec.co', 'role-contador', 'contador', json_encode(['ledger.read', 'dian.report']), 1],
    ];
    $stmt = $pdo->prepare("INSERT INTO users (id, name, email, role_id, role, permissions, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)");
    foreach ($users as $u) {
        $stmt->execute($u);
    }
}

// Seed Products if empty
$prodCount = (int)$pdo->query("SELECT COUNT(*) FROM products")->fetchColumn();
if ($prodCount === 0) {
    echo "[BACKEND SEED] Seeding Products...\n";
    $products = [
        ['prod-1', 'AB-001', 'Café Juan Valdez 500g', 'Bebidas', 28500, 21000, 24, 5, 0.19, '77020101', 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&q=80'],
        ['prod-2', 'AB-002', 'Arroz Diana Premium 1kg', 'Abarrotes', 4800, 3600, 65, 10, 0.00, '77020102', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&q=80'],
        ['prod-3', 'AB-003', 'Aceite Premier Girasol 1000ml', 'Abarrotes', 16500, 12800, 5, 10, 0.19, '77020103', 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400&q=80'],
        ['prod-4', 'LC-001', 'Leche Alquería Entera 1.1L', 'Lácteos', 4900, 3800, 42, 8, 0.00, '77020104', 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&q=80'],
        ['prod-5', 'AS-001', 'Jabón Rey Barra 300g', 'Aseo', 3200, 2200, 50, 15, 0.19, '77020105', 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80'],
        ['prod-6', 'BE-001', 'Agua Cristal con Gas 600ml', 'Bebidas', 2500, 1400, 3, 10, 0.19, '77020106', 'https://images.unsplash.com/photo-1560023907-5f339617ea30?w=400&q=80'],
        ['prod-7', 'AB-004', 'Harina PAN Blanca 1kg', 'Abarrotes', 4600, 3400, 30, 8, 0.00, '77020107', 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&q=80'],
        ['prod-8', 'SN-001', 'Papas Margarita Pollo 110g', 'Snacks', 5200, 3800, 18, 5, 0.19, '77020108', 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&q=80'],
    ];
    $stmt = $pdo->prepare("INSERT INTO products (id, sku, name, category, price, cost, stock, min_stock, iva_rate, barcode, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
    foreach ($products as $p) {
        $stmt->execute($p);
    }
}

// Seed Variants if empty
$varCount = (int)$pdo->query("SELECT COUNT(*) FROM product_variants")->fetchColumn();
if ($varCount === 0) {
    echo "[BACKEND SEED] Seeding Product Variants...\n";
    $variants = [
        ['var-1-1', 'prod-1', 'AB-001-500G', 'Café Juan Valdez Grano 500g', '7702010101', 28500, 21000, 14, 4, json_encode(['presentation' => 'Grano', 'size' => '500g']), 1, 1],
        ['var-1-2', 'prod-1', 'AB-001-MOL', 'Café Juan Valdez Molido 500g', '7702010102', 29500, 21500, 10, 4, json_encode(['presentation' => 'Molido', 'size' => '500g']), 0, 1],
        ['var-2-1', 'prod-2', 'AB-002-1KG', 'Arroz Diana Tradicional 1kg', '7702010201', 4800, 3600, 40, 15, json_encode(['presentation' => 'Tradicional', 'size' => '1kg']), 1, 1],
        ['var-2-2', 'prod-2', 'AB-002-PREM', 'Arroz Diana Premium Fortificado 1kg', '7702010202', 5400, 4000, 25, 10, json_encode(['presentation' => 'Premium', 'size' => '1kg']), 0, 1],
        ['var-8-1', 'prod-8', 'SN-001-POL', 'Papas Margarita Pollo 110g', '7702010801', 5200, 3800, 8, 4, json_encode(['flavor' => 'Pollo']), 1, 1],
        ['var-8-2', 'prod-8', 'SN-001-NAT', 'Papas Margarita Natural 110g', '7702010802', 5200, 3800, 6, 4, json_encode(['flavor' => 'Natural']), 0, 1],
        ['var-8-3', 'prod-8', 'SN-001-LIM', 'Papas Margarita Limón 110g', '7702010803', 5200, 3800, 4, 4, json_encode(['flavor' => 'Limón']), 0, 1],
    ];
    $stmt = $pdo->prepare("INSERT INTO product_variants (id, product_id, sku, name, barcode, price, cost, stock, min_stock, attributes, is_default, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
    foreach ($variants as $v) {
        $stmt->execute($v);
    }
}

// Seed Images if empty
$imgCount = (int)$pdo->query("SELECT COUNT(*) FROM product_images")->fetchColumn();
if ($imgCount === 0) {
    echo "[BACKEND SEED] Seeding Product Images...\n";
    $images = [
        ['img-1-1', 'prod-1', 'var-1-1', 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400&q=80', 1, 0, 'cafe.jpg', 'image/jpeg', 45000, 'hash-1-1'],
        ['img-2-1', 'prod-2', 'var-2-1', 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400&q=80', 1, 0, 'arroz.jpg', 'image/jpeg', 42000, 'hash-2-1'],
        ['img-3-1', 'prod-3', null, 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400&q=80', 1, 0, 'aceite.jpg', 'image/jpeg', 39000, 'hash-3-1'],
        ['img-4-1', 'prod-4', null, 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400&q=80', 1, 0, 'leche.jpg', 'image/jpeg', 41000, 'hash-4-1'],
        ['img-5-1', 'prod-5', null, 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400&q=80', 1, 0, 'jabon.jpg', 'image/jpeg', 36000, 'hash-5-1'],
        ['img-6-1', 'prod-6', null, 'https://images.unsplash.com/photo-1560023907-5f339617ea30?w=400&q=80', 1, 0, 'agua.jpg', 'image/jpeg', 38000, 'hash-6-1'],
        ['img-7-1', 'prod-7', null, 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400&q=80', 1, 0, 'harina.jpg', 'image/jpeg', 44000, 'hash-7-1'],
        ['img-8-1', 'prod-8', 'var-8-1', 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400&q=80', 1, 0, 'papas.jpg', 'image/jpeg', 48000, 'hash-8-1'],
    ];
    $stmt = $pdo->prepare("INSERT INTO product_images (id, product_id, variant_id, url, is_primary, order_pos, file_name, mime_type, file_size, file_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
    foreach ($images as $img) {
        $stmt->execute($img);
    }
}

echo "[BACKEND MIGRATION] All tables initialized and seeded successfully!\n";
