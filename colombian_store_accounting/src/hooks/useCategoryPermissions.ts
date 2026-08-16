import { UserAccount, RoleItem } from '../types/store';
import { CategoryPermissions } from '../types/category';

export function useCategoryPermissions(
  currentUser: UserAccount | null,
  roles: RoleItem[]
): CategoryPermissions {
  if (!currentUser) {
    return {
      canAddCategory: false,
      canEditCategory: false,
      canDeleteCategory: false,
      canManageCategories: false,
    };
  }

  const userRole = roles.find((r) => r.id === currentUser.roleId) ||
    roles.find((r) => r.name?.toLowerCase() === (currentUser.role || '').toLowerCase());

  const roleName = (userRole?.name || currentUser.role || '').toLowerCase();
  const isAdmin = roleName === 'admin' || currentUser.roleId === 'role-admin';
  const isContador = roleName === 'contador';

  const canManage = isAdmin || (isContador && Boolean(userRole?.modules?.includes('products')));

  return {
    canAddCategory: canManage,
    canEditCategory: canManage,
    canDeleteCategory: isAdmin,
    canManageCategories: canManage,
  };
}