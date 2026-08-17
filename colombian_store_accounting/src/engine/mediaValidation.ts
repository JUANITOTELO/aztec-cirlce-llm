import { MediaValidationError } from '../types/productMedia';

const ALLOWED_MIME_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];
const MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024; // 2MB

export function sanitizeFileName(name: string): string {
  const safe = name
    .replace(/\x00/g, '')
    .replace(/\.\.+[\\/]/g, '')
    .replace(/[^a-zA-Z0-9._-]/g, '_');
  return safe.slice(0, 100);
}

export function validateMediaFile(file: File): MediaValidationError[] {
  const errors: MediaValidationError[] = [];
  const safeName = sanitizeFileName(file.name);
  const ext = safeName.substring(safeName.lastIndexOf('.')).toLowerCase();

  if (!ALLOWED_EXTENSIONS.includes(ext) || !ALLOWED_MIME_TYPES.includes(file.type)) {
    errors.push({
      field: 'file',
      message: `Formato inválido (${file.type || ext}). Permitidos: JPG, PNG, WEBP.`,
    });
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    errors.push({
      field: 'size',
      message: `El archivo supera 2MB (Tamaño actual: ${(file.size / 1024 / 1024).toFixed(2)}MB).`,
    });
  }

  return errors;
}

export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = (err) => reject(err);
    reader.readAsDataURL(file);
  });
}