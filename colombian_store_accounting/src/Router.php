<?php

declare(strict_types=1);

namespace App;

class Router
{
    private array $routes = [];

    public function __construct(private Container $container) {}

    public function post(string $path, array $handler): void
    {
        $this->routes['POST'][$path] = $handler;
    }

    public function dispatch(): void
    {
        $method = $_SERVER['REQUEST_METHOD'];
        $path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

        $handler = $this->routes[$method][$path] ?? null;

        if (!$handler) {
            http_response_code(404);
            echo json_encode(['error' => 'Not Found']);
            return;
        }

        [$controllerClass, $methodName] = $handler;
        $controller = $this->container->get($controllerClass);

        $body = json_decode(file_get_contents('php://input'), true);

        // Simplified request object for this example
        $request = ['body' => $body];

        $controller->$methodName($request);
    }
}
