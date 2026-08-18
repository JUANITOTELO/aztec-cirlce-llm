<?php

declare(strict_types=1);

namespace App\Lib;

use Monolog\LogRecord;
use Monolog\Processor\ProcessorInterface;

/**
 * Monolog processor to redact PII from log messages and context.
 */
class PiiRedactionProcessor implements ProcessorInterface
{
    private const PII_PATTERNS = [
        // Email
        '/([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i' => '[email_redacted]',
        // Colombian Cedula (7-10 digits)
        '/\b\d{7,10}\b/' => '[id_redacted]',
        // Account numbers (example: > 5 digits)
        '/\b\d{5,}\b/' => '[number_redacted]',
    ];

    public function __invoke(LogRecord $record): LogRecord
    {
        $message = $this->redact($record->message);
        $context = $this->redactArray($record->context);

        return $record->with(message: $message, context: $context);
    }

    private function redact($data)
    {
        if (!is_string($data)) {
            return $data;
        }
        return preg_replace(array_keys(self::PII_PATTERNS), array_values(self::PII_PATTERNS), $data);
    }

    private function redactArray(array $array): array
    {
        foreach ($array as $key => &$value) {
            if (is_array($value)) {
                $value = $this->redactArray($value);
            } elseif (is_string($value)) {
                $value = $this->redact($value);
            }
        }
        return $array;
    }
}
