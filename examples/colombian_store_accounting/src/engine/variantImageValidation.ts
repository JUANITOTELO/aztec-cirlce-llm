import { ProductVariantFormData } from '../types/productVariant';
import { validateVariantPayload as baseValidateVariantPayload } from './variantCrudEngine';

export interface ValidationResult {
  isValid: boolean;
  errors: Record<string, string>;
}

export function validateVariantImageRules(
  file: File,
  currentImagesCount: number,
  maxImages: number = 10
): ValidationResult {
  const errors: Record<string, string> = {};
  if (currentImagesCount >= maxImages) {
    errors.limit = `Límite máximo de ${maxImages} imágenes alcanzado.`;
  }
  if (file.size > 3 * 1024 * 1024) {
    errors.size = 'El archivo supera el tamaño máximo permitido de 3MB.';
  }
  return {
    isValid: Object.keys(errors).length === 0,
    errors,
  };
}

export const validateVariantForm = baseValidateVariantPayload;
export const validateVariantPayload = baseValidateVariantPayload;
