export interface Category {
  id: string;
  name: string;
  description?: string;
  color?: string;
  ledgerAccountCode: string;
  ledgerAccountName: string;
  isSystem?: boolean;
  isDeleted?: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CategoryMutationPayload {
  name: string;
  description?: string;
  color?: string;
  ledgerAccountCode?: string;
  ledgerAccountName?: string;
}

export interface CategoryAuditLog {
  id?: string;
  categoryId: string;
  action: 'CREATE' | 'UPDATE' | 'DELETE' | 'RESTORE';
  userId: string;
  timestamp: string;
  details: string;
}

export interface CategoryConstraintReport {
  hasOrphans: boolean;
  orphanProductCount: number;
  orphanProductIds: string[];
  affectedCategories: string[];
  reassignmentMap: Record<string, string>;
  validationErrors: string[];
}

export interface CategoryPermissions {
  canAddCategory: boolean;
  canEditCategory: boolean;
  canDeleteCategory: boolean;
  canManageCategories: boolean;
}