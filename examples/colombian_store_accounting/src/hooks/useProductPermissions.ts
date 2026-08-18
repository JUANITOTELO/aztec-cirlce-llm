import { useMemo } from 'react';
import { UserAccount, RoleItem } from '../types/store';
import { ProductPermissions } from '../types/product';

export function useProductPermissions(currentUser: UserAccount | null | undefined, roles: RoleItem[] = []): ProductPermissions {
  return useMemo(() => {
    if (!currentUser) {
      return {
        canViewCost: false,
        canEditProduct: false,
        canAdjustStock: false,
        canDeleteProduct: false,
        canCreateProduct: false,
        canViewPricingHistory: false,
      };
    }

    const roleName = (currentUser.role || '').toLowerCase();
    const roleObj = roles.find(r => r.id === currentUser.roleId || r.name.toLowerCase() === roleName);
    const effectiveRole = roleObj ? roleObj.name.toLowerCase() : roleName;

    const isAdmin = effectiveRole === 'admin' || currentUser.roleId === 'role-admin';
    const isContador = effectiveRole === 'contador' || currentUser.roleId === 'role-contador';

    return {
      canViewCost: isAdmin || isContador,
      canEditProduct: isAdmin || isContador,
      canAdjustStock: isAdmin || isContador,
      canDeleteProduct: isAdmin,
      canCreateProduct: isAdmin || isContador,
      canViewPricingHistory: isAdmin || isContador,
    };
  }, [currentUser, roles]);
}

export function maskCostForRole(cost: number, canViewCost: boolean): string {
  if (!canViewCost) return '••••••';
  return new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(cost);
}
