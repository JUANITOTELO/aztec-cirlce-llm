<?php

declare(strict_types=1);

use Monolog\Logger;
use App\Services\LoggerService;

// Load Environment Variables
$dotenv = Dotenv\Dotenv::createImmutable(dirname(__DIR__));
$dotenv->load();

// Error and Exception Handling
ini_set('display_errors', $_ENV['APP_ENV'] === 'development' ? '1' : '0');
error_reporting(E_ALL);

set_exception_handler(function (Throwable $exception) {
    $log = LoggerService::getInstance();
    $log->error($exception->getMessage(), ['exception' => $exception]);

    http_response_code(500);
    header('Content-Type: application/problem+json');
    echo json_encode([
        'title' => 'Internal Server Error',
        'status' => 500,
        'detail' => $_ENV['APP_ENV'] === 'development' ? $exception->getMessage() : 'An unexpected error occurred.'
    ]);
});

// CORS Configuration
$allowed_origins = ['http://localhost:3000', $_ENV['APP_URL']];
if (isset($_SERVER['HTTP_ORIGIN']) && in_array($_SERVER['HTTP_ORIGIN'], $allowed_origins)) {
    header("Access-Control-Allow-Origin: {$_SERVER['HTTP_ORIGIN']}");
    header('Access-Control-Allow-Credentials: true');
}

header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}
