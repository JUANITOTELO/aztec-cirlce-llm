import { useMemo } from 'react';
import { UserAccount, RoleItem } from '../types/store';
import { ProductVariantPermissions } from '../types/productVariant';

export function useProductVariantPermissions(
  currentUser: UserAccount | null,
  roles: RoleItem[] = []
): ProductVariantPermissions {
  return useMemo(() => {
    if (!currentUser) {
      return {
        canCreateVariant: false,
        canEditVariant: false,
        canDeleteVariant: false,
        canUploadImages: false,
        canDeleteImages: false,
      };
    }

    const roleName = currentUser.role?.toLowerCase() || '';
    const roleObj = roles.find((r) => r.id === currentUser.roleId);
    const effectiveName = (roleObj?.name || roleName).toLowerCase();
    const isAdmin = effectiveName === 'admin' || currentUser.roleId === 'role-admin';
    const isContador = effectiveName === 'contador';

    return {
      canCreateVariant: isAdmin || isContador,
      canEditVariant: isAdmin || isContador,
      canDeleteVariant: isAdmin,
      canUploadImages: isAdmin || isContador,
      canDeleteImages: isAdmin,
    };
  }, [currentUser, roles]);
}