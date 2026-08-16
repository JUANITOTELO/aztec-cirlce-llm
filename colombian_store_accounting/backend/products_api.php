<?php
header('Content-Type: application/json; charset=UTF-8');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: DENY');

$method = $_SERVER['REQUEST_METHOD'];
$headers = getallheaders();
$userRole = strtolower($headers['X-User-Role'] ?? 'cajero');
$canViewCost = in_array($userRole, ['admin', 'contador'], true);

$dsn = getenv('DB_DSN') ?: 'sqlite:' . __DIR__ . '/database.sqlite';
$pdo = new PDO($dsn, getenv('DB_USER') ?: null, getenv('DB_PASS') ?: null, [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
]);

try {
    if ($method === 'GET') {
        $stmt = $pdo->query('SELECT * FROM products ORDER BY name ASC');
        $products = $stmt->fetchAll();
        foreach ($products as &$p) {
            $p['price'] = (float)$p['price'];
            $p['cost'] = $canViewCost ? (float)$p['cost'] : 0.0;
            $p['stock'] = (int)$p['stock'];
            $p['minStock'] = (int)$p['min_stock'];
            $p['ivaRate'] = (float)$p['iva_rate'];
            unset($p['min_stock'], $p['iva_rate']);
        }
        echo json_encode(['success' => true, 'data' => $products]);
        exit;
    }

    if (!in_array($userRole, ['admin', 'contador'], true)) {
        http_response_code(403);
        echo json_encode(['error' => 'Acceso no autorizado para mutaciones']);
        exit;
    }

    $input = json_decode(file_get_contents('php://input'), true);

    if ($method === 'POST') {
        $id = $input['id'] ?? ('prod_' . bin2hex(random_bytes(8)));
        $sku = strtoupper(trim($input['sku'] ?? ''));
        $name = trim($input['name'] ?? '');
        $category = trim($input['category'] ?? 'Abarrotes');
        $price = max(0, (float)($input['price'] ?? 0));
        $cost = max(0, (float)($input['cost'] ?? 0));
        $stock = max(0, (int)($input['stock'] ?? 0));
        $minStock = max(0, (int)($input['minStock'] ?? 5));
        $ivaRate = in_array((float)($input['ivaRate'] ?? 0.19), [0.0, 0.05, 0.19], true) ? (float)$input['ivaRate'] : 0.19;
        $barcode = preg_replace('/[^0-9A-Za-z-]/', '', $input['barcode'] ?? '');

        $stmt = $pdo->prepare('INSERT INTO products (id, sku, name, category, price, cost, stock, min_stock, iva_rate, barcode) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)');
        $stmt->execute([$id, $sku, $name, $category, $price, $cost, $stock, $minStock, $ivaRate, $barcode]);

        http_response_code(201);
        echo json_encode(['success' => true, 'id' => $id]);
        exit;
    }

    if ($method === 'PUT') {
        $id = $input['id'] ?? '';
        $stmt = $pdo->prepare('UPDATE products SET name = ?, category = ?, price = ?, cost = ?, stock = ?, min_stock = ?, iva_rate = ?, barcode = ? WHERE id = ?');
        $stmt->execute([
            trim($input['name'] ?? ''),
            trim($input['category'] ?? 'Abarrotes'),
            max(0, (float)($input['price'] ?? 0)),
            max(0, (float)($input['cost'] ?? 0)),
            max(0, (int)($input['stock'] ?? 0)),
            max(0, (int)($input['minStock'] ?? 5)),
            (float)($input['ivaRate'] ?? 0.19),
            preg_replace('/[^0-9A-Za-z-]/', '', $input['barcode'] ?? ''),
            $id
        ]);
        echo json_encode(['success' => true]);
        exit;
    }

    if ($method === 'DELETE') {
        $id = $_GET['id'] ?? '';
        $stmt = $pdo->prepare('DELETE FROM products WHERE id = ?');
        $stmt->execute([$id]);
        echo json_encode(['success' => true]);
        exit;
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
