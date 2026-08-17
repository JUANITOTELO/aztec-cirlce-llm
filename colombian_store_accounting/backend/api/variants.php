<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-User-Role');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$role = $_SERVER['HTTP_X_USER_ROLE'] ?? 'role-cajero';
$method = $_SERVER['REQUEST_METHOD'];
$rawInput = file_get_contents('php://input');
$data = json_decode($rawInput, true);

try {
    $pdo = new PDO('sqlite:' . __DIR__ . '/../../database.sqlite');
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->exec("CREATE TABLE IF NOT EXISTS product_variants (
        id TEXT PRIMARY KEY,
        product_id TEXT NOT NULL,
        sku TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        attributes TEXT,
        price REAL NOT NULL,
        cost REAL NOT NULL,
        stock INTEGER NOT NULL,
        min_stock INTEGER NOT NULL,
        barcode TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )");

    if ($method === 'GET') {
        $productId = $_GET['product_id'] ?? null;
        if ($productId) {
            $stmt = $pdo->prepare('SELECT * FROM product_variants WHERE product_id = :pid');
            $stmt->execute([':pid' => $productId]);
        } else {
            $stmt = $pdo->query('SELECT * FROM product_variants');
        }
        $variants = $stmt->fetchAll(PDO::FETCH_ASSOC);
        echo json_encode(['success' => true, 'data' => $variants]);
        exit;
    }

    if ($role !== 'role-admin' && $role !== 'role-contador') {
        http_response_code(403);
        echo json_encode(['success' => false, 'code' => 'FORBIDDEN', 'message' => 'Permisos insuficientes']);
        exit;
    }

    if ($method === 'POST') {
        if (empty($data['id']) || empty($data['productId']) || empty($data['sku']) || empty($data['name'])) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'Campos obligatorios faltantes']);
            exit;
        }
        $stmt = $pdo->prepare('INSERT INTO product_variants (id, product_id, sku, name, attributes, price, cost, stock, min_stock, barcode, is_active, created_at, updated_at) VALUES (:id, :pid, :sku, :name, :attrs, :price, :cost, :stock, :min_stock, :barcode, :is_active, :cat, :uat)');
        $stmt->execute([
            ':id' => $data['id'],
            ':pid' => $data['productId'],
            ':sku' => trim($data['sku']),
            ':name' => trim($data['name']),
            ':attrs' => json_encode($data['attributes'] ?? []),
            ':price' => (float)($data['price'] ?? 0),
            ':cost' => (float)($data['cost'] ?? 0),
            ':stock' => (int)($data['stock'] ?? 0),
            ':min_stock' => (int)($data['minStock'] ?? 0),
            ':barcode' => $data['barcode'] ?? null,
            ':is_active' => !empty($data['isActive']) ? 1 : 0,
            ':cat' => date('c'),
            ':uat' => date('c'),
        ]);
        echo json_encode(['success' => true, 'id' => $data['id']]);
        exit;
    }

    if ($method === 'DELETE') {
        $id = $_GET['id'] ?? $data['id'] ?? null;
        if (!$id) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'ID no proporcionado']);
            exit;
        }
        $stmt = $pdo->prepare('DELETE FROM product_variants WHERE id = :id');
        $stmt->execute([':id' => $id]);
        echo json_encode(['success' => true, 'deleted' => $id]);
        exit;
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'message' => $e->getMessage()]);
}
