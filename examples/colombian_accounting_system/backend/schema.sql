-- SIFCO - Esquema MySQL 8.0 para Sistema Contable Colombiano
CREATE DATABASE IF NOT EXISTS `sifco_contable` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `sifco_contable`;

CREATE TABLE `companies` (
  `id` VARCHAR(36) PRIMARY KEY,
  `nit` VARCHAR(20) NOT NULL UNIQUE,
  `dv` CHAR(1) NOT NULL,
  `business_name` VARCHAR(255) NOT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE `accounting_periods` (
  `id` VARCHAR(36) PRIMARY KEY,
  `company_id` VARCHAR(36) NOT NULL,
  `period` VARCHAR(7) NOT NULL, -- YYYY-MM
  `is_closed` TINYINT(1) NOT NULL DEFAULT 0,
  `closed_at` DATETIME NULL,
  `closed_by` VARCHAR(36) NULL,
  UNIQUE KEY `uk_company_period` (`company_id`, `period`),
  FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE `consecutive_sequences` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `company_id` VARCHAR(36) NOT NULL,
  `voucher_type` VARCHAR(50) NOT NULL,
  `current_value` BIGINT NOT NULL DEFAULT 0,
  `prefix` VARCHAR(10) NOT NULL,
  UNIQUE KEY `uk_company_voucher_type` (`company_id`, `voucher_type`),
  FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`)
) ENGINE=InnoDB;

CREATE TABLE `vouchers` (
  `id` VARCHAR(36) PRIMARY KEY,
  `company_id` VARCHAR(36) NOT NULL,
  `consecutive` VARCHAR(50) NOT NULL,
  `voucher_type` VARCHAR(50) NOT NULL,
  `transaction_date` DATE NOT NULL,
  `period` VARCHAR(7) NOT NULL,
  `status` ENUM('BORRADOR', 'REVISADO', 'APROBADO', 'CONTABILIZADO', 'ANULADO') NOT NULL DEFAULT 'BORRADOR',
  `notes` TEXT NULL,
  `created_by` VARCHAR(36) NOT NULL,
  `approved_by` VARCHAR(36) NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`company_id`) REFERENCES `companies`(`id`),
  INDEX `idx_company_period` (`company_id`, `period`)
) ENGINE=InnoDB;

CREATE TABLE `voucher_lines` (
  `id` VARCHAR(36) PRIMARY KEY,
  `voucher_id` VARCHAR(36) NOT NULL,
  `account_code` VARCHAR(20) NOT NULL,
  `third_party_nit` VARCHAR(20) NOT NULL,
  `third_party_name` VARCHAR(255) NOT NULL,
  `concept` VARCHAR(255) NOT NULL,
  `base_amount` DECIMAL(18, 4) NOT NULL DEFAULT 0.0000,
  `debit` DECIMAL(18, 4) NOT NULL DEFAULT 0.0000,
  `credit` DECIMAL(18, 4) NOT NULL DEFAULT 0.0000,
  FOREIGN KEY (`voucher_id`) REFERENCES `vouchers`(`id`) ON DELETE CASCADE,
  INDEX `idx_account_code` (`account_code`)
) ENGINE=InnoDB;