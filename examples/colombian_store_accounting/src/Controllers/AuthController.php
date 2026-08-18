<?php

declare(strict_types=1);

namespace App\Controllers;

use App\Services\TokenService;
use App\Services\LoggerService;
use Predis\Client as RedisClient;

class AuthController
{
    private const MAX_LOGIN_ATTEMPTS = 5;
    private const LOCKOUT_TIME_SECONDS = 900; // 15 minutes

    public function __construct(
        private TokenService $tokenService,
        private RedisClient $redis,
        private LoggerService $logger
    ) {}

    public function login(array $request): void
    {
        $username = $request['body']['username'] ?? '';
        $ip = $_SERVER['REMOTE_ADDR'];
        $rateLimitKey = "login_attempts:{$ip}";
        $lockoutKey = "login_lockout:{$username}";

        if ($this->redis->get($lockoutKey)) {
            $this->logger->warning('Login attempt for locked account', ['username' => $username, 'ip' => $ip]);
            http_response_code(429);
            echo json_encode(['error' => 'Account locked due to too many failed attempts.']);
            return;
        }

        // Dummy user validation
        if ($username === 'admin' && ($request['body']['password'] ?? '') === 'password') { // In real app, use password_verify
            $this->redis->del([$rateLimitKey, "failed_attempts:{$username}"]);
            $this->logger->info('Successful login', ['username' => $username]);
            $this->issueTokens(1, 'Admin');
        } else {
            $this->handleFailedLogin($username, $ip, $lockoutKey, $rateLimitKey);
        }
    }

    private function handleFailedLogin(string $username, string $ip, string $lockoutKey, string $rateLimitKey): void
    {
        $this->logger->warning('Failed login attempt', ['username' => $username, 'ip' => $ip]);

        $attempts = $this->redis->incr("failed_attempts:{$username}");
        $this->redis->incr($rateLimitKey);
        $this->redis->expire($rateLimitKey, 300); // 5 min window for IP rate limit

        if ($attempts >= self::MAX_LOGIN_ATTEMPTS) {
            $this->redis->setex($lockoutKey, self::LOCKOUT_TIME_SECONDS, 'locked');
        }

        http_response_code(401);
        echo json_encode(['error' => 'Invalid credentials']);
    }

    private function issueTokens(int $userId, string $role): void
    {
        $tokens = $this->tokenService->generateTokens(['userId' => $userId, 'role' => $role]);

        setcookie(
            'refresh_token',
            $tokens['refreshToken'],
            [
                'expires' => time() + (86400 * 7), // 7 days
                'path' => '/api/auth/refresh',
                'httponly' => true,
                'secure' => $_ENV['APP_ENV'] === 'production',
                'samesite' => 'Strict'
            ]
        );

        header('Content-Type: application/json');
        echo json_encode(['accessToken' => $tokens['accessToken']]);
    }

    public function refresh(): void
    {
        // Implementation for refresh token logic
        // ...
    }

    public function logout(): void
    {
        // Implementation for logout (add tokens to revocation list)
        // ...
    }
}
