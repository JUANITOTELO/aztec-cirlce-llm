export type ImageType = 'PRIMARY' | 'GALLERY' | 'THUMBNAIL' | 'VARIANT';

export interface ProductImage {
  id: string;
  productId: string;
  variantId?: string | null;
  imageType?: ImageType;
  url: string;
  altText?: string;
  order?: number;
  fileSize?: number;
  mimeType?: string;
  createdAt?: string;
  isPrimary?: boolean;
  fileName?: string;
}

export interface MediaValidationError {
  field?: string;
  message?: string;
  isValid?: boolean;
  error?: string;
}

export interface ImageUploadPayload {
  productId: string;
  variantId?: string | null;
  file: File;
  altText?: string;
  isPrimary?: boolean;
}