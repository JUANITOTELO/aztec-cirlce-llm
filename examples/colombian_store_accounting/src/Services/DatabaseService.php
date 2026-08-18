<?php

declare(strict_types=1);

namespace App\Services;

use PDO;
use PDOException;

/**
 * Database Service with security-hardened configuration.
 * - Enforces SSL/TLS connections.
 * - Disables emulated prepares to prevent SQL injection.
 * - Sets default transaction isolation level to SERIALIZABLE for ACID compliance.
 * - Note on Pooling: True connection pooling is managed by the server (e.g., pgbouncer, proxysql)
 *   or by using persistent connections (PDO::ATTR_PERSISTENT), which has caveats in a web context.
 *   This implementation focuses on secure, per-request connections.
 */
class DatabaseService
{
    private ?PDO $pdo = null;

    public function __construct()
    {
        $dsn = sprintf(
            'mysql:host=%s;port=%d;dbname=%s;charset=%s',
            $_ENV['DB_HOST'],
            $_ENV['DB_PORT'],
            $_ENV['DB_DATABASE'],
            $_ENV['DB_CHARSET']
        );

        // Security-focused PDO options
        $options = [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false, // CRITICAL for security
            PDO::ATTR_PERSISTENT         => false, // Set to true for persistent connections if env supports it
            
            // Enforce SSL/TLS connection
            PDO::MYSQL_ATTR_SSL_CA      => $_ENV['DB_SSL_CA'],
            PDO::MYSQL_ATTR_SSL_CERT    => $_ENV['DB_SSL_CERT'],
            PDO::MYSQL_ATTR_SSL_KEY     => $_ENV['DB_SSL_KEY'],
            PDO::MYSQL_ATTR_SSL_VERIFY_SERVER_CERT => false, // Set to true in prod with proper certs

            // Set transaction isolation level upon connection
            PDO::MYSQL_ATTR_INIT_COMMAND => 'SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE'
        ];

        try {
            $this->pdo = new PDO($dsn, $_ENV['DB_USERNAME'], $_ENV['DB_PASSWORD'], $options);
        } catch (PDOException $e) {
            // In a real app, log this securely without credentials
            throw new PDOException('Database connection failed: ' . $e->getMessage());
        }
    }

    public function getConnection(): PDO
    {
        return $this->pdo;
    }
}
