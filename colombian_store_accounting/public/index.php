<?php

declare(strict_types=1);

require_once dirname(__DIR__) . '/vendor/autoload.php';
require_once dirname(__DIR__) . '/src/bootstrap.php';

use App\Container;
use App\Router;
use App\Controllers\AuthController;
use App\Controllers\TransactionController;

// Initialize DI Container
$container = new Container();

// Initialize Router
$router = new Router($container);

// Define Routes
$router->post('/api/auth/login', [AuthController::class, 'login']);
$router->post('/api/auth/refresh', [AuthController::class, 'refresh']);
$router->post('/api/auth/logout', [AuthController::class, 'logout']);

$router->post('/api/pos/sync', [TransactionController::class, 'sync']);

// Dispatch Request
$router->dispatch();
