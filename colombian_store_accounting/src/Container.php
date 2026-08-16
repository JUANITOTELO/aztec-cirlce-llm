<?php

declare(strict_types=1);

namespace App;

use App\Services\DatabaseService;
use App\Services\LedgerService;
use App\Services\DianService;
use App\Services\TokenService;
use App\Services\LoggerService;
use Predis\Client as RedisClient;
use ReflectionClass;

class Container
{
    private array $instances = [];

    public function __construct()
    {
        // Eagerly instantiate singletons
        $this->instances[LoggerService::class] = LoggerService::getInstance();
        $this->instances[DatabaseService::class] = new DatabaseService();
        $this->instances[RedisClient::class] = new RedisClient([
            'scheme' => 'tcp',
            'host'   => $_ENV['REDIS_HOST'],
            'port'   => $_ENV['REDIS_PORT'],
        ]);
    }

    public function get(string $class)
    {
        if (isset($this->instances[$class])) {
            return $this->instances[$class];
        }

        $reflector = new ReflectionClass($class);
        $constructor = $reflector->getConstructor();

        if (!$constructor) {
            return new $class();
        }

        $dependencies = [];
        foreach ($constructor->getParameters() as $param) {
            $dependencyClass = $param->getType()->getName();
            $dependencies[] = $this->get($dependencyClass);
        }

        $instance = new $class(...$dependencies);
        $this->instances[$class] = $instance;
        return $instance;
    }
}
