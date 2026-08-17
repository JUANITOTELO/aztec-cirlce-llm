<?php
declare(strict_types=1);

/**
 * Aztec Colombian Store & Accounting REST API Router
 * Production-ready standalone SQLite REST backend
 */

// Set CORS and JSON Headers
header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-User-Role');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

$dbPath = __DIR__ . '/database.sqlite';
try {
    $pdo = new PDO("sqlite:{$dbPath}", null, null, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Database connection failed: ' . $e->getMessage()]);
    exit;
}

$method = $_SERVER['REQUEST_METHOD'];
$uri = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);

// Normalize route (strip optional /api prefix)
$route = preg_replace('#^/api#', '', $uri);
$route = '/' . trim($route, '/');

$input = json_decode(file_get_contents('php://input') ?: '{}', true) ?: [];

function jsonResponse(mixed $data, int $status = 200): void {
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}

// ----------------------------------------------------
// Health Check
// ----------------------------------------------------
if ($route === '/health' || $route === '/') {
    jsonResponse([
        'status' => 'healthy',
        'backend' => 'Aztec Colombian Store Backend API (SQLite)',
        'timestamp' => date('c'),
        'database' => 'connected',
    ]);
}

// ----------------------------------------------------
// Full State Sync (/sync/all)
// ----------------------------------------------------
if ($route === '/sync/all') {
    if ($method === 'GET') {
        $products = $pdo->query("SELECT * FROM products ORDER BY name ASC")->fetchAll();
        $variants = $pdo->query("SELECT * FROM product_variants ORDER BY sku ASC")->fetchAll();
        $images = $pdo->query("SELECT * FROM product_images ORDER BY order_pos ASC")->fetchAll();
        $categories = $pdo->query("SELECT * FROM categories ORDER BY name ASC")->fetchAll();
        $sales = $pdo->query("SELECT * FROM sales ORDER BY created_at DESC LIMIT 100")->fetchAll();
        $ledger = $pdo->query("SELECT * FROM ledger_entries ORDER BY date DESC, created_at DESC LIMIT 200")->fetchAll();
        $users = $pdo->query("SELECT * FROM users ORDER BY name ASC")->fetchAll();
        $roles = $pdo->query("SELECT * FROM roles ORDER BY name ASC")->fetchAll();

        foreach ($variants as &$v) {
            $v['attributes'] = json_decode($v['attributes'] ?: '{}', true);
            $v['isDefault'] = (bool)$v['is_default'];
            $v['isActive'] = (bool)$v['is_active'];
            $v['productId'] = $v['product_id'];
            $v['minStock'] = (int)$v['min_stock'];
            unset($v['is_default'], $v['is_active'], $v['product_id'], $v['min_stock']);
        }
        foreach ($images as &$img) {
            $img['isPrimary'] = (bool)$img['is_primary'];
            $img['order'] = (int)$img['order_pos'];
            $img['productId'] = $img['product_id'];
            $img['variantId'] = $img['variant_id'];
            $img['fileHash'] = $img['file_hash'];
            $img['fileName'] = $img['file_name'];
            $img['fileSize'] = $img['file_size'];
            $img['mimeType'] = $img['mime_type'];
            unset($img['is_primary'], $img['order_pos'], $img['product_id'], $img['variant_id'], $img['file_hash'], $img['file_name'], $img['file_size'], $img['mime_type']);
        }
        foreach ($products as &$p) {
            $p['minStock'] = (int)$p['min_stock'];
            $p['ivaRate'] = (float)$p['iva_rate'];
            unset($p['min_stock'], $p['iva_rate']);
        }
        foreach ($users as &$u) {
            $u['roleId'] = $u['role_id'];
            $u['permissions'] = json_decode($u['permissions'] ?: '[]', true);
            $u['isActive'] = (bool)$u['is_active'];
            unset($u['role_id'], $u['is_active']);
        }
        foreach ($roles as &$r) {
            $r['modules'] = json_decode($r['modules'] ?: '[]', true);
            $r['isSystem'] = (bool)$r['is_system'];
            unset($r['is_system']);
        }

        jsonResponse([
            'success' => true,
            'data' => [
                'products' => $products,
                'variants' => $variants,
                'images' => $images,
                'categories' => $categories,
                'sales' => $sales,
                'ledgerEntries' => $ledger,
                'users' => $users,
                'roles' => $roles,
            ],
            'timestamp' => date('c'),
        ]);
    }

    if ($method === 'POST') {
        $pdo->beginTransaction();
        try {
            if (!empty($input['products'])) {
                $stmt = $pdo->prepare("INSERT OR REPLACE INTO products (id, sku, name, category, price, cost, stock, min_stock, iva_rate, barcode, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
                foreach ($input['products'] as $p) {
                    $stmt->execute([
                        $p['id'],
                        $p['sku'],
                        $p['name'],
                        $p['category'] ?? 'Abarrotes',
                        $p['price'] ?? 0,
                        $p['cost'] ?? 0,
                        $p['stock'] ?? 0,
                        $p['minStock'] ?? 5,
                        $p['ivaRate'] ?? 0.19,
                        $p['barcode'] ?? null,
                        $p['image'] ?? null,
                    ]);
                }
            }
            if (!empty($input['variants'])) {
                $stmt = $pdo->prepare("INSERT OR REPLACE INTO product_variants (id, product_id, sku, name, barcode, price, cost, stock, min_stock, attributes, is_default, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
                foreach ($input['variants'] as $v) {
                    $stmt->execute([
                        $v['id'],
                        $v['productId'] ?? $v['product_id'],
                        $v['sku'],
                        $v['name'],
                        $v['barcode'] ?? null,
                        $v['price'] ?? 0,
                        $v['cost'] ?? 0,
                        $v['stock'] ?? 0,
                        $v['minStock'] ?? 0,
                        is_array($v['attributes'] ?? null) ? json_encode($v['attributes']) : ($v['attributes'] ?? '{}'),
                        !empty($v['isDefault']) ? 1 : 0,
                        $v['isActive'] !== false ? 1 : 0,
                    ]);
                }
            }
            if (!empty($input['images'])) {
                $stmt = $pdo->prepare("INSERT OR REPLACE INTO product_images (id, product_id, variant_id, url, is_primary, order_pos, file_name, mime_type, file_size, file_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
                foreach ($input['images'] as $img) {
                    $stmt->execute([
                        $img['id'],
                        $img['productId'] ?? $img['product_id'] ?? '',
                        $img['variantId'] ?? $img['variant_id'] ?? null,
                        $img['url'],
                        !empty($img['isPrimary']) ? 1 : 0,
                        $img['order'] ?? $img['order_pos'] ?? 0,
                        $img['fileName'] ?? $img['file_name'] ?? null,
                        $img['mimeType'] ?? $img['mime_type'] ?? 'image/webp',
                        $img['fileSize'] ?? $img['file_size'] ?? 1024,
                        $img['fileHash'] ?? $img['file_hash'] ?? ('hash-' . $img['id']),
                    ]);
                }
            }
            if (!empty($input['categories'])) {
                $stmt = $pdo->prepare("INSERT OR REPLACE INTO categories (id, name, description, color) VALUES (?, ?, ?, ?)");
                foreach ($input['categories'] as $c) {
                    $stmt->execute([
                        $c['id'],
                        $c['name'],
                        $c['description'] ?? '',
                        $c['color'] ?? '#3B82F6',
                    ]);
                }
            }
            $pdo->commit();
            jsonResponse(['success' => true, 'message' => 'Full state synced to backend database']);
        } catch (Exception $e) {
            $pdo->rollBack();
            jsonResponse(['error' => 'Sync failed: ' . $e->getMessage()], 500);
        }
    }
}

// ----------------------------------------------------
// Products (/products)
// ----------------------------------------------------
if ($route === '/products') {
    if ($method === 'GET') {
        $products = $pdo->query("SELECT * FROM products ORDER BY name ASC")->fetchAll();
        foreach ($products as &$p) {
            $p['minStock'] = (int)$p['min_stock'];
            $p['ivaRate'] = (float)$p['iva_rate'];
            unset($p['min_stock'], $p['iva_rate']);
        }
        jsonResponse(['success' => true, 'data' => $products]);
    }
    if ($method === 'POST') {
        $id = $input['id'] ?? ('prod-' . bin2hex(random_bytes(6)));
        $stmt = $pdo->prepare("INSERT OR REPLACE INTO products (id, sku, name, category, price, cost, stock, min_stock, iva_rate, barcode, image) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
        $stmt->execute([
            $id,
            $input['sku'] ?? '',
            $input['name'] ?? '',
            $input['category'] ?? 'Abarrotes',
            (float)($input['price'] ?? 0),
            (float)($input['cost'] ?? 0),
            (int)($input['stock'] ?? 0),
            (int)($input['minStock'] ?? 5),
            (float)($input['ivaRate'] ?? 0.19),
            $input['barcode'] ?? null,
            $input['image'] ?? null,
        ]);
        jsonResponse(['success' => true, 'id' => $id, 'data' => array_merge($input, ['id' => $id])], 201);
    }
}

// Product by ID (/products/{id})
if (preg_match('#^/products/([^/]+)$#', $route, $matches)) {
    $productId = $matches[1];
    if ($method === 'GET') {
        $stmt = $pdo->prepare("SELECT * FROM products WHERE id = ?");
        $stmt->execute([$productId]);
        $prod = $stmt->fetch();
        if (!$prod) jsonResponse(['error' => 'Product not found'], 404);
        $prod['minStock'] = (int)$prod['min_stock'];
        $prod['ivaRate'] = (float)$prod['iva_rate'];
        unset($prod['min_stock'], $prod['iva_rate']);
        jsonResponse(['success' => true, 'data' => $prod]);
    }
    if ($method === 'PUT') {
        $stmt = $pdo->prepare("UPDATE products SET sku = ?, name = ?, category = ?, price = ?, cost = ?, stock = ?, min_stock = ?, iva_rate = ?, barcode = ?, image = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?");
        $stmt->execute([
            $input['sku'] ?? '',
            $input['name'] ?? '',
            $input['category'] ?? 'Abarrotes',
            (float)($input['price'] ?? 0),
            (float)($input['cost'] ?? 0),
            (int)($input['stock'] ?? 0),
            (int)($input['minStock'] ?? 5),
            (float)($input['ivaRate'] ?? 0.19),
            $input['barcode'] ?? null,
            $input['image'] ?? null,
            $productId,
        ]);
        jsonResponse(['success' => true, 'id' => $productId, 'data' => array_merge($input, ['id' => $productId])]);
    }
    if ($method === 'DELETE') {
        $stmt = $pdo->prepare("DELETE FROM products WHERE id = ?");
        $stmt->execute([$productId]);
        jsonResponse(['success' => true, 'message' => "Product {$productId} deleted"]);
    }
}

// ----------------------------------------------------
// Variants (/products/{id}/variants)
// ----------------------------------------------------
if (preg_match('#^/products/([^/]+)/variants$#', $route, $matches)) {
    $productId = $matches[1];
    if ($method === 'GET') {
        $stmt = $pdo->prepare("SELECT * FROM product_variants WHERE product_id = ? ORDER BY sku ASC");
        $stmt->execute([$productId]);
        $variants = $stmt->fetchAll();
        foreach ($variants as &$v) {
            $v['attributes'] = json_decode($v['attributes'] ?: '{}', true);
            $v['isDefault'] = (bool)$v['is_default'];
            $v['isActive'] = (bool)$v['is_active'];
            $v['productId'] = $v['product_id'];
            $v['minStock'] = (int)$v['min_stock'];
            unset($v['is_default'], $v['is_active'], $v['product_id'], $v['min_stock']);
        }
        jsonResponse(['success' => true, 'data' => $variants]);
    }
    if ($method === 'POST') {
        $id = $input['id'] ?? ('var-' . bin2hex(random_bytes(4)));
        $stmt = $pdo->prepare("INSERT OR REPLACE INTO product_variants (id, product_id, sku, name, barcode, price, cost, stock, min_stock, attributes, is_default, is_active) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
        $stmt->execute([
            $id,
            $productId,
            $input['sku'] ?? '',
            $input['name'] ?? '',
            $input['barcode'] ?? null,
            (float)($input['price'] ?? 0),
            (float)($input['cost'] ?? 0),
            (int)($input['stock'] ?? 0),
            (int)($input['minStock'] ?? 0),
            is_array($input['attributes'] ?? null) ? json_encode($input['attributes']) : ($input['attributes'] ?? '{}'),
            !empty($input['isDefault']) ? 1 : 0,
            $input['isActive'] !== false ? 1 : 0,
        ]);
        jsonResponse(['success' => true, 'id' => $id, 'data' => array_merge($input, ['id' => $id, 'productId' => $productId])], 201);
    }
}

// ----------------------------------------------------
// Images (/products/{id}/images)
// ----------------------------------------------------
if (preg_match('#^/products/([^/]+)/images$#', $route, $matches)) {
    $productId = $matches[1];
    if ($method === 'GET') {
        $stmt = $pdo->prepare("SELECT * FROM product_images WHERE product_id = ? ORDER BY order_pos ASC");
        $stmt->execute([$productId]);
        $images = $stmt->fetchAll();
        foreach ($images as &$img) {
            $img['isPrimary'] = (bool)$img['is_primary'];
            $img['order'] = (int)$img['order_pos'];
            $img['productId'] = $img['product_id'];
            $img['variantId'] = $img['variant_id'];
            $img['fileHash'] = $img['file_hash'];
            $img['fileName'] = $img['file_name'];
            $img['fileSize'] = $img['file_size'];
            $img['mimeType'] = $img['mime_type'];
            unset($img['is_primary'], $img['order_pos'], $img['product_id'], $img['variant_id'], $img['file_hash'], $img['file_name'], $img['file_size'], $img['mime_type']);
        }
        jsonResponse(['success' => true, 'data' => $images]);
    }
    if ($method === 'POST') {
        $id = $input['id'] ?? ('img-' . bin2hex(random_bytes(4)));
        $stmt = $pdo->prepare("INSERT OR REPLACE INTO product_images (id, product_id, variant_id, url, is_primary, order_pos, file_name, mime_type, file_size, file_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
        $stmt->execute([
            $id,
            $productId,
            $input['variantId'] ?? null,
            $input['url'] ?? '',
            !empty($input['isPrimary']) ? 1 : 0,
            (int)($input['order'] ?? 0),
            $input['fileName'] ?? null,
            $input['mimeType'] ?? 'image/webp',
            (int)($input['fileSize'] ?? 1024),
            $input['fileHash'] ?? ('hash-' . $id),
        ]);
        jsonResponse(['success' => true, 'id' => $id, 'data' => array_merge($input, ['id' => $id, 'productId' => $productId])], 201);
    }
}

// ----------------------------------------------------
// Categories (/categories)
// ----------------------------------------------------
if ($route === '/categories') {
    if ($method === 'GET') {
        $categories = $pdo->query("SELECT * FROM categories ORDER BY name ASC")->fetchAll();
        jsonResponse(['success' => true, 'data' => $categories]);
    }
    if ($method === 'POST') {
        $id = $input['id'] ?? ('cat-' . bin2hex(random_bytes(4)));
        $stmt = $pdo->prepare("INSERT OR REPLACE INTO categories (id, name, description, color) VALUES (?, ?, ?, ?)");
        $stmt->execute([
            $id,
            $input['name'] ?? '',
            $input['description'] ?? '',
            $input['color'] ?? '#3B82F6',
        ]);
        jsonResponse(['success' => true, 'id' => $id, 'data' => array_merge($input, ['id' => $id])], 201);
    }
}

// ----------------------------------------------------
// Sales & POS Invoices (/sales & /pos/sync)
// ----------------------------------------------------
if ($route === '/sales' || $route === '/pos/sync') {
    if ($method === 'GET') {
        $sales = $pdo->query("SELECT * FROM sales ORDER BY created_at DESC LIMIT 100")->fetchAll();
        jsonResponse(['success' => true, 'data' => $sales]);
    }
    if ($method === 'POST') {
        $pdo->beginTransaction();
        try {
            $saleId = $input['id'] ?? ('inv-' . bin2hex(random_bytes(6)));
            $invNum = $input['invoiceNumber'] ?? ('FAC-' . date('Ymd') . '-' . substr(bin2hex(random_bytes(2)), 0, 4));
            $subtotal = (float)($input['subtotal'] ?? 0);
            $ivaTotal = (float)($input['ivaTotal'] ?? ($input['totalIva'] ?? 0));
            $total = (float)($input['total'] ?? ($subtotal + $ivaTotal));
            $payMethod = $input['paymentMethod'] ?? 'Efectivo';
            $custName = $input['customerName'] ?? 'Consumidor Final';
            $custDoc = $input['customerDoc'] ?? ($input['customerNit'] ?? '222222222222');

            // 1. Insert Sale record
            $stmt = $pdo->prepare("INSERT OR REPLACE INTO sales (id, invoice_number, customer_id, customer_name, customer_doc, subtotal, iva_total, total, payment_method, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
            $stmt->execute([$saleId, $invNum, $input['customerId'] ?? null, $custName, $custDoc, $subtotal, $ivaTotal, $total, $payMethod, 'COMPLETED']);

            // 2. Insert items and decrement stock
            if (!empty($input['items']) && is_array($input['items'])) {
                $itemStmt = $pdo->prepare("INSERT INTO sale_items (id, sale_id, product_id, variant_id, sku, name, quantity, unit_price, unit_cost, iva_rate, line_total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
                $stockUpdate = $pdo->prepare("UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?");
                
                foreach ($input['items'] as $it) {
                    $prod = $it['product'] ?? $it;
                    $prodId = $prod['id'] ?? '';
                    $qty = (int)($it['quantity'] ?? 1);
                    $price = (float)($prod['price'] ?? 0);
                    $cost = (float)($prod['cost'] ?? 0);
                    $iva = (float)($prod['ivaRate'] ?? 0.19);
                    $lineTotal = $qty * $price;

                    $itemStmt->execute([
                        'sitem-' . bin2hex(random_bytes(4)),
                        $saleId,
                        $prodId,
                        $it['variantId'] ?? null,
                        $prod['sku'] ?? '',
                        $prod['name'] ?? '',
                        $qty,
                        $price,
                        $cost,
                        $iva,
                        $lineTotal,
                    ]);

                    if ($prodId) {
                        $stockUpdate->execute([$qty, $prodId]);
                    }
                }
            }

            // 3. Automated Colombian PUC Double-Entry Ledger rows
            // Account 1105 (Caja / Efectivo) or 1110 (Bancos) [DEBIT = total]
            $ledgerStmt = $pdo->prepare("INSERT INTO ledger_entries (id, date, puc_code, puc_name, description, debit, credit, reference) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
            $pucAsset = ($payMethod === 'Efectivo') ? '110505' : '111005';
            $pucAssetName = ($payMethod === 'Efectivo') ? 'Caja General' : 'Bancos Nacionales';
            $today = date('Y-m-d');

            $ledgerStmt->execute(['ledg-' . bin2hex(random_bytes(4)), $today, $pucAsset, $pucAssetName, "Venta POS {$invNum} - {$payMethod}", $total, 0.0, $invNum]);
            
            // Account 4135 (Comercio al por mayor y menor) [CREDIT = subtotal]
            $ledgerStmt->execute(['ledg-' . bin2hex(random_bytes(4)), $today, '413505', 'Comercio al por mayor y menor', "Ingreso por venta {$invNum}", 0.0, $subtotal, $invNum]);
            
            // Account 2408 (Impuesto sobre las ventas por pagar - IVA) [CREDIT = ivaTotal]
            if ($ivaTotal > 0) {
                $ledgerStmt->execute(['ledg-' . bin2hex(random_bytes(4)), $today, '240801', 'IVA Generado en Ventas 19%', "IVA generado venta {$invNum}", 0.0, $ivaTotal, $invNum]);
            }

            $pdo->commit();
            jsonResponse([
                'success' => true,
                'saleId' => $saleId,
                'invoiceNumber' => $invNum,
                'total' => $total,
                'message' => 'Sale processed and accounting ledger updated successfully',
            ], 201);
        } catch (Exception $e) {
            $pdo->rollBack();
            jsonResponse(['error' => 'Sale processing failed: ' . $e->getMessage()], 500);
        }
    }
}

// ----------------------------------------------------
// Ledger Entries (/ledger)
// ----------------------------------------------------
if ($route === '/ledger') {
    if ($method === 'GET') {
        $ledger = $pdo->query("SELECT * FROM ledger_entries ORDER BY date DESC, created_at DESC LIMIT 500")->fetchAll();
        jsonResponse(['success' => true, 'data' => $ledger]);
    }
    if ($method === 'POST') {
        $id = $input['id'] ?? ('ledg-' . bin2hex(random_bytes(4)));
        $stmt = $pdo->prepare("INSERT INTO ledger_entries (id, date, puc_code, puc_name, description, debit, credit, reference) VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
        $stmt->execute([
            $id,
            $input['date'] ?? date('Y-m-d'),
            $input['pucCode'] ?? $input['puc_code'] ?? '110505',
            $input['pucName'] ?? $input['puc_name'] ?? 'Caja General',
            $input['description'] ?? '',
            (float)($input['debit'] ?? 0),
            (float)($input['credit'] ?? 0),
            $input['reference'] ?? null,
        ]);
        jsonResponse(['success' => true, 'id' => $id], 201);
    }
}

// Fallback 404
jsonResponse(['error' => "Endpoint not found: {$method} {$route}"], 404);
