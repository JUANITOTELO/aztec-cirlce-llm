<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/vendor/autoload.php';
require_once dirname(__DIR__) . '/src/bootstrap.php';

use App\Container;
use App\Router;
use App\Controllers\AuthController;
use App\Controllers\TransactionController;
use App\Controllers\ProductImageController;
use App\Controllers\ProductVariantController;
use App\Middleware\AuthMiddleware;
use App\Middleware\RoleMiddleware;

// Initialize DI Container
$container = new Container();

// Initialize Router
$router = new Router($container);

// Define Routes
$router->post('/api/auth/login', [AuthController::class, 'login']);
$router->post('/api/auth/refresh', [AuthController::class, 'refresh']);
$router->post('/api/auth/logout', [AuthController::class, 'logout']);

$router->post('/api/pos/sync', [TransactionController::class, 'sync']);

// Product Variant Routes
$router->get('/api/products/{id}/variants', [ProductVariantController::class, 'getVariants']);
$router->post('/api/products/{id}/variants', [ProductVariantController::class, 'create']);
$router->put('/api/products/{id}/variants/{variantId}', [ProductVariantController::class, 'update']);
$router->delete('/api/products/{id}/variants/{variantId}', [ProductVariantController::class, 'delete']);

// Product Media Routes
$router->post('/api/products/{id}/images', [ProductImageController::class, 'upload']);
$router->delete('/api/products/{id}/images/{imageId}', [ProductImageController::class, 'delete']);
$router->dispatch();
