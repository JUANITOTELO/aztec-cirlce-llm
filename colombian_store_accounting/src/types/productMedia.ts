export type ImageType = 'PRIMARY' | 'GALLERY' | 'THUMBNAIL' | 'VARIANT';

export interface ProductImage {
  id: string;
  productId: string;
  variantId?: string | null;
  imageType?: ImageType;
  url: string;
  altText?: string;
  order: number;
  fileSize?: number;
  mimeType?: string;
  createdAt?: string;
  isPrimary?: boolean;
  fileName?: string;
  fileHash?: string;
  dimensions?: { width: number; height: number };
  status?: 'pending' | 'synced' | 'error';
}

export interface MediaValidationIssue {
  field?: string;
  message: string;
  isValid?: boolean;
  error?: string;
}

export interface ImageUploadPayload {
  productId: string;
  variantId?: string | null;
  file?: File;
  files?: File[];
  altText?: string;
  isPrimary?: boolean;
}