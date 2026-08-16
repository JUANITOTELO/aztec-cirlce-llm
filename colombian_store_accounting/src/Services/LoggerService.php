<?php

declare(strict_types=1);

namespace App\Services;

use Monolog\Logger;
use Monolog\Handler\StreamHandler;
use App\Lib\PiiRedactionProcessor;

class LoggerService extends Logger
{
    private static ?LoggerService $instance = null;

    public function __construct()
    {
        parent::__construct('app');
        $logLevel = Logger::toMonologLevel($_ENV['LOG_LEVEL'] ?? 'INFO');
        
        $handler = new StreamHandler('php://stdout', $logLevel);
        $handler->pushProcessor(new PiiRedactionProcessor());
        
        $this->pushHandler($handler);
    }

    public static function getInstance(): LoggerService
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }
}
