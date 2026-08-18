import React, { useState } from 'react';
import { ProductVariant } from '../../types/productVariant';
import { UserAccount, Product } from '../../types/store';
import { MediaProvider } from '../../context/MediaContext';
import { ProductMediaManagerModal } from './ProductMediaManagerModal';
import { VariantEditModal } from './VariantEditModal';

export interface ProductMediaCoordinatorProps {
  product?: Product;
  productId?: string;
  variants?: ProductVariant[];
  currentUser?: UserAccount;
  isMediaModalOpen?: boolean;
  isVariantModalOpen?: boolean;
  editingVariant?: ProductVariant | null;
  onCloseMediaModal?: () => void;
  onCloseVariantModal?: () => void;
  onSaveVariant?: (variant: ProductVariant) => void;
  onDeleteVariant?: (variantId: string) => void;
  inline?: boolean;
}

const fallbackUser: UserAccount = {
  id: 'usr-admin',
  name: 'Administrador',
  email: 'admin@pos.local',
  roleId: 'role-admin',
  role: 'admin',
  permissions: ['*'],
  isActive: true,
};

export const ProductMediaCoordinator: React.FC<ProductMediaCoordinatorProps> = ({
  product,
  productId,
  variants = [],
  currentUser = fallbackUser,
  isMediaModalOpen: controlledMediaOpen,
  isVariantModalOpen: controlledVariantOpen,
  editingVariant = null,
  onCloseMediaModal,
  onCloseVariantModal,
  onSaveVariant = () => {},
  onDeleteVariant = () => {},
  inline = false,
}) => {
  const [internalMediaOpen, setInternalMediaOpen] = useState(true);
  const [internalVariantOpen, setInternalVariantOpen] = useState(false);

  const isMediaOpen = controlledMediaOpen !== undefined ? controlledMediaOpen : internalMediaOpen;
  const isVariantOpen = controlledVariantOpen !== undefined ? controlledVariantOpen : internalVariantOpen;

  const handleCloseMediaModal = () => {
    setInternalMediaOpen(false);
    onCloseMediaModal?.();
  };

  const handleCloseVariantModal = () => {
    setInternalVariantOpen(false);
    onCloseVariantModal?.();
  };

  const resolvedProductId = product?.id || productId || '';
  const resolvedProduct: Product = product || {
    id: resolvedProductId,
    name: 'Producto',
    sku: 'SKU-001',
    category: 'General',
    price: 0,
    cost: 0,
    stock: 0,
    minStock: 5,
    ivaRate: 0.19,
  };

  return (
    <MediaProvider productId={resolvedProductId} variants={variants} currentUser={currentUser}>
      {isMediaOpen && (
        <ProductMediaManagerModal
          product={resolvedProduct}
          variants={variants}
          currentUser={currentUser}
          onClose={handleCloseMediaModal}
          inline={inline}
        />
      )}
      {isVariantOpen && (
        <VariantEditModal
          isOpen={isVariantOpen}
          onClose={handleCloseVariantModal}
          onSave={onSaveVariant}
          onDelete={onDeleteVariant}
          variant={editingVariant}
          productId={resolvedProductId}
          currentUser={currentUser}
        />
      )}
    </MediaProvider>
  );
};
