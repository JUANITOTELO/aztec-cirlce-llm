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
-- Product Variants
CREATE TABLE IF NOT EXISTS `product_variants` (
  `id` VARCHAR(64) PRIMARY KEY,
  `product_id` VARCHAR(64) NOT NULL,
  `sku` VARCHAR(64) NOT NULL UNIQUE,
  `name` VARCHAR(255) NOT NULL,
  `barcode` VARCHAR(64) DEFAULT NULL,
  `price` DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
  `cost` DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
  `stock` INT NOT NULL DEFAULT 0,
  `min_stock` INT NOT NULL DEFAULT 0,
  `attributes` JSON DEFAULT NULL,
  `is_default` TINYINT(1) NOT NULL DEFAULT 0,
  `is_active` TINYINT(1) NOT NULL DEFAULT 1,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Product Media Catalog
CREATE TABLE IF NOT EXISTS `product_images` (
  `id` VARCHAR(64) PRIMARY KEY,
  `product_id` VARCHAR(64) NOT NULL,
  `variant_id` VARCHAR(64) DEFAULT NULL,
  `url` MEDIUMTEXT NOT NULL,
  `is_primary` TINYINT(1) NOT NULL DEFAULT 0,
  `order_pos` INT UNSIGNED NOT NULL DEFAULT 1,
  `file_name` VARCHAR(255) DEFAULT NULL,
  `mime_type` VARCHAR(64) DEFAULT NULL,
  `file_size` INT UNSIGNED DEFAULT NULL,
  `file_hash` CHAR(64) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_prod_media` (`product_id`, `order_pos`),
  INDEX `idx_variant_media` (`variant_id`, `order_pos`),
  UNIQUE KEY `idx_product_file_hash` (`product_id`, `file_hash`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
