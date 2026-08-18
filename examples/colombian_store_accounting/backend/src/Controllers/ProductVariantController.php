<?php

declare(strict_types=1);

namespace App\Controllers;

class ProductVariantController
{
    public function getVariants(string $productId): void
    {
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'success',
            'productId' => $productId,
            'data' => []
        ]);
    }

    public function create(string $productId): void
    {
        $payload = json_decode(file_get_contents('php://input'), true) ?? [];
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'success',
            'message' => 'Variant created successfully',
            'data' => array_merge(['id' => 'var-' . bin2hex(random_bytes(4)), 'productId' => $productId], $payload)
        ]);
    }

    public function update(string $productId, string $variantId): void
    {
        $payload = json_decode(file_get_contents('php://input'), true) ?? [];
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'success',
            'message' => 'Variant updated',
            'data' => array_merge(['id' => $variantId, 'productId' => $productId], $payload)
        ]);
    }

    public function delete(string $productId, string $variantId): void
    {
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'success',
            'message' => "Variant {$variantId} deleted successfully"
        ]);
    }
}
