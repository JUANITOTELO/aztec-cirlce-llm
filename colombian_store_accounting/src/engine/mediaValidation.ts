export interface ValidationError {
  field: string;
  message: string;
}

const ALLOWED_MIME_TYPES = new Set([
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/webp',
  'video/mp4',
  'video/webm',
  'audio/mpeg',
  'audio/wav',
]);

const ALLOWED_EXTENSIONS = new Set([
  'jpg',
  'jpeg',
  'png',
  'gif',
  'webp',
  'mp4',
  'webm',
  'mp3',
  'wav',
]);

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

/**
 * Sanitizes a file name to prevent path traversal attacks.
 * - Strips all directory components (handles both '/' and '\\' separators).
 * - Removes any remaining '..' sequences.
 * - Strips characters that are unsafe in file names.
 */
export function sanitizeFileName(fileName: string): string {
  if (!fileName) {
    return '';
  }

  // Normalize separators and take only the last path segment (the base name).
  const segments = fileName.replace(/\\/g, '/').split('/');
  let baseName = segments[segments.length - 1] ?? '';

  // Remove any remaining parent-directory sequences.
  while (baseName.includes('..')) {
    baseName = baseName.replace(/\.\./g, '');
  }

  // Remove characters that are unsafe or reserved in file names.
  baseName = baseName.replace(/[<>:"|?*\x00-\x1f]/g, '');

  // Collapse leading dots to avoid hidden/relative name tricks.
  baseName = baseName.replace(/^\.+/, '');

  return baseName.trim();
}

function getExtension(fileName: string): string {
  const idx = fileName.lastIndexOf('.');
  if (idx === -1 || idx === fileName.length - 1) {
    return '';
  }
  return fileName.slice(idx + 1).toLowerCase();
}

/**
 * Validates a media file against an allow-list of MIME types and extensions,
 * and enforces a maximum file size.
 */
export function validateMediaFile(file: File): ValidationError[] {
  const errors: ValidationError[] = [];

  const safeName = sanitizeFileName(file.name);
  const extension = getExtension(safeName);

  if (!ALLOWED_MIME_TYPES.has(file.type)) {
    errors.push({
      field: 'file',
      message: `Unsupported MIME type: ${file.type || 'unknown'}`,
    });
  }

  if (!ALLOWED_EXTENSIONS.has(extension)) {
    errors.push({
      field: 'file',
      message: `Unsupported file extension: ${extension || 'none'}`,
    });
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    errors.push({
      field: 'file',
      message: `File exceeds maximum size of ${MAX_FILE_SIZE_BYTES} bytes`,
    });
  }

  if (file.size === 0) {
    errors.push({
      field: 'file',
      message: 'File is empty',
    });
  }

  return errors;
}
