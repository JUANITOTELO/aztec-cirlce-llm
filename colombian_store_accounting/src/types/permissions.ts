export type SystemPermission =
  | 'products:view'
  | 'products:create'
  | 'products:edit'
  | 'products:delete'
  | 'products:edit:variants'
  | 'products:edit:media'
  | 'inventory:adjust'
  | 'accounting:view';

export interface RolePermissionMatrix {
  [roleId: string]: SystemPermission[];
}

export const DEFAULT_ROLE_PERMISSIONS: RolePermissionMatrix = {
  'role-admin': [
    'products:view',
    'products:create',
    'products:edit',
    'products:delete',
    'products:edit:variants',
    'products:edit:media',
    'inventory:adjust',
    'accounting:view'
  ],
  'role-cajero': ['products:view'],
  'role-contador': ['products:view', 'products:edit', 'inventory:adjust', 'accounting:view']
};

export function hasPermission(roleId: string | undefined, perm: SystemPermission): boolean {
  if (!roleId) return false;
  const permissions = DEFAULT_ROLE_PERMISSIONS[roleId] || [];
  return permissions.includes(perm);
}
