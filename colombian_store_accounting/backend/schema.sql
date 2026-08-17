-- Aztec Decision Circle Backend Schema v2
CREATE TABLE IF NOT EXISTS `products` (
  `id` VARCHAR(64) PRIMARY KEY,
  `sku` VARCHAR(64) NOT NULL UNIQUE,
  `name` VARCHAR(255) NOT NULL,
  `category` VARCHAR(100) NOT NULL,
  `price` DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
  `cost` DECIMAL(18, 2) NOT NULL DEFAULT 0.00,
  `stock` INT NOT NULL DEFAULT 0,
  `min_stock` INT NOT NULL DEFAULT 5,
  `iva_rate` DECIMAL(5, 2) NOT NULL DEFAULT 0.19,
  `barcode` VARCHAR(64) DEFAULT NULL,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT `fk_be_pv_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

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
  CONSTRAINT `fk_be_pi_product` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_be_pi_variant` FOREIGN KEY (`variant_id`) REFERENCES `product_variants` (`id`) ON DELETE CASCADE,
  INDEX `idx_be_prod_media` (`product_id`, `order_pos`),
  INDEX `idx_be_variant_media` (`variant_id`, `order_pos`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
