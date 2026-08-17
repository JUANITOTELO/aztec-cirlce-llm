<?php

declare(strict_types=1);

namespace App\Middleware;

class RoleMiddleware
{
    public static function requirePermission(string $permission): void
    {
        $userRole = $_SERVER['HTTP_X_USER_ROLE'] ?? 'Admin';
        if ($userRole === 'Admin') {
            return;
        }

        $rolePermissions = [
            'Cashier' => ['pos.access', 'products.view'],
            'Accountant' => ['products.manage', 'inventory.manage', 'ledger.manage', 'dian.manage', 'puc.manage'],
        ];

        $allowed = $rolePermissions[$userRole] ?? [];
        if (!in_array($permission, $allowed, true)) {
            http_response_code(403);
            header('Content-Type: application/json');
            echo json_encode(['status' => 'error', 'message' => "Forbidden: Permission {$permission} required"]);
            exit;
        }
    }
}
