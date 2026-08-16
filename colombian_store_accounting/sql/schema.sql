-- Aztec Decision Circle Accounting System Schema v2

-- Users and Roles
CREATE TABLE `users` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `username` VARCHAR(50) NOT NULL UNIQUE,
  `password_hash` VARCHAR(255) NOT NULL,
  `role` ENUM('Admin', 'Cashier', 'Accountant') NOT NULL,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Immutable PUC Chart of Accounts with Versioning
CREATE TABLE `puc_versions` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `version_name` VARCHAR(100) NOT NULL,
  `valid_from` DATE NOT NULL,
  `valid_to` DATE,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE `puc_accounts` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `puc_version_id` INT UNSIGNED NOT NULL,
  `account_code` VARCHAR(20) NOT NULL,
  `account_name` VARCHAR(255) NOT NULL,
  `is_control_account` BOOLEAN NOT NULL DEFAULT FALSE,
  FOREIGN KEY (`puc_version_id`) REFERENCES `puc_versions`(`id`),
  UNIQUE KEY `puc_version_code` (`puc_version_id`, `account_code`)
) ENGINE=InnoDB;

-- Core Transactions Table with Idempotency Key
CREATE TABLE `transactions` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `client_transaction_id` CHAR(36) NOT NULL UNIQUE COMMENT 'Client-generated UUID for idempotency',
  `user_id` INT UNSIGNED NOT NULL,
  `puc_version_id` INT UNSIGNED NOT NULL,
  `transaction_date` DATETIME NOT NULL,
  `description` TEXT,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),
  FOREIGN KEY (`puc_version_id`) REFERENCES `puc_versions`(`id`)
) ENGINE=InnoDB;

-- Double-Entry Ledger
CREATE TABLE `ledger_entries` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `transaction_id` INT UNSIGNED NOT NULL,
  `account_code` VARCHAR(20) NOT NULL,
  `debit` DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
  `credit` DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
  FOREIGN KEY (`transaction_id`) REFERENCES `transactions`(`id`),
  INDEX `account_code_idx` (`account_code`)
) ENGINE=InnoDB;

-- Immutable Append-Only Transaction Journal for Auditing
CREATE TABLE `transaction_journal` (
  `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `entry_timestamp` TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),
  `actor_user_id` INT UNSIGNED NOT NULL,
  `action` VARCHAR(50) NOT NULL, -- e.g., 'CREATE_TRANSACTION', 'DIAN_SUBMIT'
  `payload` JSON NOT NULL,
  `previous_entry_hash` CHAR(64) COMMENT 'SHA-256 hash of the previous entry for chaining',
  `entry_hash` CHAR(64) NOT NULL UNIQUE COMMENT 'SHA-256 hash of this entry'
) ENGINE=InnoDB;

-- DIAN Submission Log
CREATE TABLE `dian_submissions_log` (
  `id` INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  `submission_id` CHAR(36) NOT NULL UNIQUE,
  `user_id` INT UNSIGNED NOT NULL,
  `status` ENUM('PENDING', 'SUBMITTED', 'CONFIRMED', 'FAILED') NOT NULL,
  `request_payload` TEXT NOT NULL,
  `request_signature` TEXT NOT NULL,
  `response_payload` TEXT,
  `submitted_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `confirmed_at` TIMESTAMP NULL,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)
) ENGINE=InnoDB;
