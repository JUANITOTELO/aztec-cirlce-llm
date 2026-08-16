-- Aztec Accounting & POS Database Schema
-- RBAC: Roles, Permissions, Modules and User Access Control

CREATE TABLE IF NOT EXISTS roles (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    is_system TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS permissions (
    id VARCHAR(64) PRIMARY KEY,
    module VARCHAR(50) NOT NULL,
    feature_key VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id VARCHAR(64) NOT NULL,
    permission_id VARCHAR(64) NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id VARCHAR(64) NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- Insert Base Roles
INSERT INTO roles (id, name, description, is_system)
VALUES 
    ('role-admin', 'Admin', 'Acceso total y configuración de usuarios, roles y módulos del sistema', 1),
    ('role-cajero', 'Cajero', 'Acceso a facturación POS y consulta de existencias', 1),
    ('role-contador', 'Contador', 'Acceso a libros contables, PUC, inventario y DIAN', 1)
ON DUPLICATE KEY UPDATE 
    description = VALUES(description),
    is_system = VALUES(is_system);

-- Insert Feature Permissions
INSERT INTO permissions (id, module, feature_key, description) VALUES
    ('perm-pos-all', 'pos', 'pos.access', 'Acceso completo al módulo Punto de Venta POS'),
    ('perm-inv-all', 'inventory', 'inventory.manage', 'Gestión de productos, existencias y alertas de stock'),
    ('perm-led-all', 'ledger', 'ledger.manage', 'Consulta y registro de asientos en libro diario/mayor'),
    ('perm-dian-all', 'dian', 'dian.manage', 'Liquidación tributaria y reportes DIAN (IVA, ReteFuente, ReteICA)'),
    ('perm-puc-all', 'puc', 'puc.manage', 'Administración y consulta del catálogo de cuentas PUC'),
    ('perm-usr-view', 'users', 'users.view', 'Ver lista de usuarios y roles del sistema'),
    ('perm-usr-manage', 'users', 'users.manage', 'Crear, editar, eliminar y asignar roles a usuarios'),
    ('perm-role-config', 'users', 'roles.configure_access', 'Configurar roles y matriz de accesos a módulos')
ON DUPLICATE KEY UPDATE 
    module = VALUES(module),
    description = VALUES(description);

-- Assign all permissions and feature access to the Admin role
INSERT IGNORE INTO role_permissions (role_id, permission_id)
SELECT 'role-admin', id FROM permissions;

-- Ensure default Admin user is registered with role-admin
INSERT INTO users (id, name, email, password_hash, role_id, is_active)
VALUES (
    'usr-admin',
    'Administrador General',
    'admin@aztec.co',
    '$2y$10$vQc4569P4fK5aD9qX2I9eeR8k1c2oF0zY.XzJ091xOqQW8f7mYkGm',
    'role-admin',
    1
)
ON DUPLICATE KEY UPDATE 
    role_id = 'role-admin',
    is_active = 1;
