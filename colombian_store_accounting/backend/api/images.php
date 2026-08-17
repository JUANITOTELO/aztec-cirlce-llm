<?php
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-User-Role');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$role = $_SERVER['HTTP_X_USER_ROLE'] ?? 'role-cajero';
$method = $_SERVER['REQUEST_METHOD'];
$data = json_decode(file_get_contents('php://input'), true);

try {
    $pdo = new PDO('sqlite:' . __DIR__ . '/../../database.sqlite');
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->exec("CREATE TABLE IF NOT EXISTS product_images (
        id TEXT PRIMARY KEY,
        product_id TEXT NOT NULL,
        variant_id TEXT,
        url TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        mime_type TEXT NOT NULL,
        is_primary INTEGER NOT NULL DEFAULT 0,
        order_index INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL
    )");

    if ($method === 'GET') {
        $productId = $_GET['product_id'] ?? null;
        if ($productId) {
            $stmt = $pdo->prepare('SELECT * FROM product_images WHERE product_id = :pid ORDER BY order_index ASC');
            $stmt->execute([':pid' => $productId]);
        } else {
            $stmt = $pdo->query('SELECT * FROM product_images');
        }
        echo json_encode(['success' => true, 'data' => $stmt->fetchAll(PDO::FETCH_ASSOC)]);
        exit;
    }

    if ($role !== 'role-admin' && $role !== 'role-contador') {
        http_response_code(403);
        echo json_encode(['success' => false, 'message' => 'Permisos insuficientes']);
        exit;
    }

    if ($method === 'POST') {
        if (empty($data['id']) || empty($data['productId']) || empty($data['url'])) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'Datos de imagen incompletos']);
            exit;
        }
        $allowedMimes = ['image/jpeg', 'image/png', 'image/webp'];
        $mime = $data['mimeType'] ?? 'image/jpeg';
        if (!in_array($mime, $allowedMimes)) {
            http_response_code(400);
            echo json_encode(['success' => false, 'message' => 'MIME type no soportado']);
            exit;
        }
        $stmt = $pdo->prepare('INSERT INTO product_images (id, product_id, variant_id, url, file_name, file_size, mime_type, is_primary, order_index, created_at) VALUES (:id, :pid, :vid, :url, :fname, :fsize, :mime, :is_pri, :ord, :cat)');
        $stmt->execute([
            ':id' => $data['id'],
            ':pid' => $data['productId'],
            ':vid' => $data['variantId'] ?? null,
            ':url' => $data['url'],
            ':fname' => $data['fileName'] ?? 'image.png',
            ':fsize' => (int)($data['fileSize'] ?? 0),
            ':mime' => $mime,
            ':is_pri' => !empty($data['isPrimary']) ? 1 : 0,
            ':ord' => (int)($data['order'] ?? 0),
            ':cat' => date('c'),
        ]);
        echo json_encode(['success' => true, 'id' => $data['id']]);
        exit;
    }

    if ($method === 'DELETE') {
        $id = $_GET['id'] ?? $data['id'] ?? null;
        $stmt = $pdo->prepare('DELETE FROM product_images WHERE id = :id');
        $stmt->execute([':id' => $id]);
        echo json_encode(['success' => true, 'deleted' => $id]);
        exit;
    }
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['success' => false, 'message' => $e->getMessage()]);
}
