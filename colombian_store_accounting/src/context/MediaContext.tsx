import React, { createContext, useContext, ReactNode } from 'react';
import { ProductImage, ImageUploadPayload } from '../types/productMedia';
import { ProductVariant } from '../types/productVariant';
import { UserAccount } from '../types/store';
import { useMediaOrchestrator } from '../hooks/useMediaOrchestrator';

export interface MediaContextValue {
  images: ProductImage[];
  isLoading: boolean;
  isUploading: boolean;
  error: string | null;
  selectedVariantId: string | null;
  setSelectedVariantId: (id: string | null) => void;
  uploadImages: (payload: ImageUploadPayload) => Promise<ProductImage[]>;
  deleteImage: (imageId: string, user?: UserAccount) => Promise<void>;
  assignImageToVariant: (imageId: string, variantId: string | null, user?: UserAccount) => Promise<void>;
  reorderImages?: (imageIds: string[]) => void;
  setPrimaryImage?: (imageId: string, user?: UserAccount) => Promise<void>;
  clearError?: () => void;
}

const defaultMediaContext: MediaContextValue = {
  images: [],
  isLoading: false,
  isUploading: false,
  error: null,
  selectedVariantId: null,
  setSelectedVariantId: () => {},
  uploadImages: async () => [],
  deleteImage: async () => {},
  assignImageToVariant: async () => {},
  reorderImages: () => {},
  setPrimaryImage: async () => {},
  clearError: () => {},
};

const MediaContext = createContext<MediaContextValue | undefined>(undefined);

export interface MediaProviderProps {
  children: ReactNode;
  productId?: string;
  variants?: ProductVariant[];
  user?: UserAccount;
  currentUser?: UserAccount;
  initialImages?: ProductImage[];
  onImagesUpdated?: (images: ProductImage[]) => void;
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

export const MediaProvider: React.FC<MediaProviderProps> = ({
  children,
  productId = '',
  variants = [],
  user,
  currentUser,
  initialImages,
  onImagesUpdated,
}) => {
  const orchestrator = useMediaOrchestrator({
    productId: productId || '',
    variants: variants || [],
    currentUser: currentUser || user || fallbackUser,
    initialImages,
    onImagesUpdated,
  });

  return (
    <MediaContext.Provider value={orchestrator as unknown as MediaContextValue}>
      {children}
    </MediaContext.Provider>
  );
};

export const useMediaContext = (): MediaContextValue => {
  const context = useContext(MediaContext);
  return context || defaultMediaContext;
};

export const useMedia = useMediaContext;

export default MediaContext;
