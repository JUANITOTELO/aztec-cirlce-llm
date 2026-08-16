-- Aztec ERP - Production Ready Schema for Product & Inventory Management
CREATE TABLE IF NOT EXISTS products (
    id VARCHAR(64) PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL DEFAULT 'Abarrotes',
    price DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    cost DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    stock INT NOT NULL DEFAULT 0,
    min_stock INT NOT NULL DEFAULT 5,
    iva_rate DECIMAL(4, 2) NOT NULL DEFAULT 0.19,
    barcode VARCHAR(64) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_iva_rate CHECK (iva_rate IN (0.00, 0.05, 0.19)),
    CONSTRAINT chk_positive_price CHECK (price >= 0),
    CONSTRAINT chk_positive_cost CHECK (cost >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_barcode ON products(barcode);
CREATE INDEX idx_products_category ON products(category);

CREATE TABLE IF NOT EXISTS product_pricing_history (
    id VARCHAR(64) PRIMARY KEY,
    product_id VARCHAR(64) NOT NULL,
    sku VARCHAR(50) NOT NULL,
    old_price DECIMAL(14, 2) NOT NULL,
    new_price DECIMAL(14, 2) NOT NULL,
    old_cost DECIMAL(14, 2) NOT NULL,
    new_cost DECIMAL(14, 2) NOT NULL,
    old_iva_rate DECIMAL(4, 2) NOT NULL,
    new_iva_rate DECIMAL(4, 2) NOT NULL,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(255) NOT NULL,
    CONSTRAINT fk_pricing_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX idx_pricing_hist_prod ON product_pricing_history(product_id);
