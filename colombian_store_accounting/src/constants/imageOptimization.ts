export const IMAGE_OPTIMIZATION_CONFIG = {
  MAX_WIDTH: 1200,
  MAX_HEIGHT: 1200,
  COMPRESSION_QUALITY: 0.82,
  MAX_FILE_SIZE_BYTES: 3 * 1024 * 1024,
  CRITICAL_QUOTA_THRESHOLD: 0.85,
  ALLOWED_MIME_TYPES: ['image/jpeg', 'image/png', 'image/webp'] as const,
  MAGIC_BYTES: {
    JPEG: [0xff, 0xd8, 0xff],
    PNG: [0x89, 0x50, 0x4e, 0x47],
    WEBP: [0x52, 0x49, 0x46, 0x46],
  },
};
