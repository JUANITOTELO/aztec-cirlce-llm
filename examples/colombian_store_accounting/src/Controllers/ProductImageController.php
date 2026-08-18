<?php

declare(strict_types=1);

namespace App\Controllers;

class ProductImageController
{
    private string $uploadDir;

    public function __construct()
    {
        $this->uploadDir = dirname(__DIR__, 2) . '/public/uploads/products/';
        if (!is_dir($this->uploadDir)) {
            mkdir($this->uploadDir, 0755, true);
        }
    }

    public function upload(string $id): void
    {
        header('Content-Type: application/json; charset=utf-8');
        
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
            http_response_code(405);
            echo json_encode(['error' => 'Method not allowed']);
            return;
        }

        if (empty($_FILES['image'])) {
            http_response_code(400);
            echo json_encode(['error' => 'No image file supplied']);
            return;
        }

        $file = $_FILES['image'];
        $maxBytes = 5 * 1024 * 1024;
        if ($file['size'] > $maxBytes) {
            http_response_code(413);
            echo json_encode(['error' => 'File size exceeds 5MB limit']);
            return;
        }

        $allowedMimes = ['image/jpeg', 'image/png', 'image/webp'];
        $finfo = new \finfo(FILEINFO_MIME_TYPE);
        $mime = $finfo->file($file['tmp_name']);
        if (!in_array($mime, $allowedMimes, true)) {
            http_response_code(415);
            echo json_encode(['error' => 'Invalid file format. Supported: JPG, PNG, WEBP']);
            return;
        }

        $fileHash = hash_file('sha256', $file['tmp_name']);
        $ext = pathinfo($file['name'], PATHINFO_EXTENSION);
        $safeName = sprintf('%s_%s.%s', $id, bin2hex(random_bytes(8)), $ext);
        $destination = $this->uploadDir . $safeName;

        if (!move_uploaded_file($file['tmp_name'], $destination)) {
            http_response_code(500);
            echo json_encode(['error' => 'Failed to persist uploaded media']);
            return;
        }

        $variantId = $_POST['variant_id'] ?? null;
        echo json_encode([
            'success' => true,
            'data' => [
                'id' => 'img_' . bin2hex(random_bytes(6)),
                'product_id' => $id,
                'variant_id' => $variantId,
                'file_name' => $file['name'],
                'url' => '/uploads/products/' . $safeName,
                'file_hash' => $fileHash,
                'mime_type' => $mime,
                'file_size' => $file['size']
            ]
        ]);
    }

    public function delete(string $id, string $imageId): void
    {
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode([
            'success' => true,
            'deleted_id' => $imageId,
            'product_id' => $id
        ]);
    }
}