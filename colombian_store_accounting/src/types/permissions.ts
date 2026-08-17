export type SystemPermission =
  | 'pos.access'
  | 'inventory.manage'
  | 'ledger.manage'
  | 'dian.manage'
  | 'puc.manage'
  | 'products.manage_media'
  | 'products.upload_media'
  | 'users.view'
  | 'users.manage'
  | 'roles.configure_access';

export interface RolePermissionMatrix {
  roleId: string;
  roleName: string;
  permissions: SystemPermission[];
}

export const DEFAULT_ROLE_PERMISSIONS: Record<string, SystemPermission[]> = {
  'role-admin': [
    'pos.access',
    'inventory.manage',
    'ledger.manage',
    'dian.manage',
    'puc.manage',
    'products.manage_media',
    'products.upload_media',
    'users.view',
    'users.manage',
    'roles.configure_access'
  ],
  'role-administrador': [
    'pos.access',
    'inventory.manage',
    'ledger.manage',
    'dian.manage',
    'puc.manage',
    'products.manage_media',
    'products.upload_media',
    'users.view',
    'users.manage',
    'roles.configure_access'
  ],
  'role-contador': [
    'pos.access',
    'inventory.manage',
    'ledger.manage',
    'dian.manage',
    'puc.manage',
    'products.manage_media',
    'products.upload_media'
  ],
  'role-supervisor': [
    'pos.access',
    'inventory.manage',
    'products.manage_media',
    'products.upload_media'
  ],
  'role-cajero': [
    'pos.access'
  ]
};

export const hasPermission = (
  user: { role?: string; roleId?: string; permissions?: string[] } | null | undefined,
  permission: SystemPermission
): boolean => {
  if (!user) return false;
  const rawRole = (user.role || '').toLowerCase().trim();
  const rawRoleId = (user.roleId || '').toLowerCase().trim();
  const normalizedRoleId = rawRoleId || (rawRole ? (rawRole.startsWith('role-') ? rawRole : `role-${rawRole}`) : '');

  if (
    rawRole === 'admin' ||
    rawRole === 'administrador' ||
    normalizedRoleId === 'role-admin' ||
    normalizedRoleId === 'role-administrador'
  ) {
    return true;
  }

  if (Array.isArray(user.permissions)) {
    if (user.permissions.includes('*') || user.permissions.includes('all')) return true;
    if (user.permissions.includes(permission)) return true;
    const [domain] = permission.split('.');
    if (domain && user.permissions.includes(`${domain}.*`)) return true;
  }

  const perms =
    DEFAULT_ROLE_PERMISSIONS[normalizedRoleId] ||
    DEFAULT_ROLE_PERMISSIONS[`role-${rawRole}`] ||
    DEFAULT_ROLE_PERMISSIONS[rawRole] ||
    [];

  return perms.includes(permission);
};
