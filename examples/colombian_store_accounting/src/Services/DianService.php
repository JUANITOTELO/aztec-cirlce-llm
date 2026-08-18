<?php

declare(strict_types=1);

namespace App\Services;

use Exception;

/**
 * DIAN Service for tax settlement submissions.
 * Implements RSA-SHA256 signing and mTLS with certificate pinning.
 */
class DianService
{
    private string $privateKey;
    private string $dianPublicKey;

    public function __construct(private LoggerService $logger)
    {
        $this->privateKey = file_get_contents($_ENV['DIAN_PRIVATE_KEY_PATH']);
        $this->dianPublicKey = file_get_contents($_ENV['DIAN_PUBLIC_KEY_PATH']);
    }

    /**
     * Signs a payload with the company's private key using RSA-SHA256.
     */
    public function signPayload(string $payload): string
    {
        $signature = '';
        if (!openssl_sign($payload, $signature, $this->privateKey, OPENSSL_ALGO_SHA256)) {
            throw new Exception('Failed to sign DIAN payload.');
        }
        return base64_encode($signature);
    }

    /**
     * Validates an incoming payload signature from DIAN.
     */
    public function validatePayload(string $payload, string $base64Signature): bool
    {
        $signature = base64_decode($base64Signature);
        $result = openssl_verify($payload, $signature, $this->dianPublicKey, OPENSSL_ALGO_SHA256);
        return $result === 1;
    }

    /**
     * Submits a settlement to DIAN with mTLS and certificate pinning.
     */
    public function submitSettlement(string $payload): array
    {
        $signature = $this->signPayload($payload);
        $url = $_ENV['DIAN_API_URL'] . '/settlements';

        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $payload);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'X-Signature: ' . $signature
        ]);

        // mTLS and Certificate Pinning Configuration
        curl_setopt($ch, CURLOPT_SSLCERT, $_ENV['DB_SSL_CERT']);
        curl_setopt($ch, CURLOPT_SSLKEY, $_ENV['DB_SSL_KEY']);
        curl_setopt($ch, CURLOPT_CAINFO, $_ENV['DB_SSL_CA']);
        curl_setopt($ch, CURLOPT_PINNEDPUBLICKEY, $_ENV['DIAN_PINNED_PUBLIC_KEY']);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);

        if ($error) {
            $this->logger->error('DIAN submission cURL error', ['error' => $error]);
            throw new Exception('DIAN API request failed: ' . $error);
        }

        // Log submission to immutable journal
        // ...

        return ['status' => $httpCode, 'body' => json_decode($response, true)];
    }
}
