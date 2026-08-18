<?php

declare(strict_types=1);

namespace App\Middleware;

class AuthMiddleware
{
    public static function verify(): void
    {
        $headers = getallheaders();
        $authHeader = $headers['Authorization'] ?? $headers['authorization'] ?? '';

        if (!str_starts_with($authHeader, 'Bearer ') && empty($_SERVER['HTTP_AUTHORIZATION'])) {
            // Fallback for session/mock headers during development
            if (isset($_SERVER['HTTP_X_USER_ID'])) {
                return;
            }
            http_response_code(401);
            header('Content-Type: application/json');
            echo json_encode(['status' => 'error', 'message' => 'Unauthorized: Missing or invalid token']);
            exit;
        }
    }
}
