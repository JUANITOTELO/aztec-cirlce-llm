import { IMAGE_OPTIMIZATION_CONFIG as CFG } from '../constants/imageOptimization';

export type MediaErrorCode = 'INVALID_MIME' | 'INVALID_MAGIC' | 'FILE_TOO_LARGE' | 'QUOTA_EXCEEDED' | 'CANVAS_ERROR';

export interface OptimizedImageData {
  base64: string;
  width: number;
  height: number;
  sizeBytes: number;
}

export class MediaValidationError extends Error {
  constructor(public code: MediaErrorCode, message: string) {
    super(message);
    this.name = 'MediaValidationError';
  }
}

export async function validateImageBuffer(file: File): Promise<void> {
  if (!CFG.ALLOWED_MIME_TYPES.includes(file.type as any)) {
    throw new MediaValidationError('INVALID_MIME', `Formato no permitido: ${file.type}`);
  }
  if (file.size > CFG.MAX_FILE_SIZE_BYTES) {
    throw new MediaValidationError('FILE_TOO_LARGE', `El archivo supera 3MB (${(file.size / 1024 / 1024).toFixed(1)}MB)`);
  }
  const headerBytes = new Uint8Array(await file.slice(0, 4).arrayBuffer());
  const isJpeg = headerBytes[0] === 0xff && headerBytes[1] === 0xd8 && headerBytes[2] === 0xff;
  const isPng = headerBytes[0] === 0x89 && headerBytes[1] === 0x50 && headerBytes[2] === 0x4e && headerBytes[3] === 0x47;
  const isWebp = headerBytes[0] === 0x52 && headerBytes[1] === 0x49 && headerBytes[2] === 0x46 && headerBytes[3] === 0x46;
  if (!isJpeg && !isPng && !isWebp) {
    throw new MediaValidationError('INVALID_MAGIC', 'El archivo no contiene bytes de cabecera válidos de imagen.');
  }
}

export async function compressAndOptimizeImage(file: File): Promise<OptimizedImageData> {
  await validateImageBuffer(file);
  if (navigator.storage && navigator.storage.estimate) {
    const { usage = 0, quota = 1 } = await navigator.storage.estimate();
    if (usage / quota > CFG.CRITICAL_QUOTA_THRESHOLD) {
      throw new MediaValidationError('QUOTA_EXCEEDED', 'Almacenamiento del navegador superó el 85% de capacidad.');
    }
  }
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      try {
        URL.revokeObjectURL(url);
        let { width, height } = img;
        if (width > CFG.MAX_WIDTH || height > CFG.MAX_HEIGHT) {
          const ratio = Math.min(CFG.MAX_WIDTH / width, CFG.MAX_HEIGHT / height);
          width = Math.round(width * ratio);
          height = Math.round(height * ratio);
        }
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (!ctx) return reject(new MediaValidationError('CANVAS_ERROR', 'No se pudo inicializar contexto 2D.'));
        ctx.drawImage(img, 0, 0, width, height);
        const base64DataUrl = canvas.toDataURL('image/webp', CFG.COMPRESSION_QUALITY);
        const sizeBytes = Math.round((base64DataUrl.length * 3) / 4);
        resolve({ base64: base64DataUrl, width, height, sizeBytes });
      } catch (err) {
        reject(new MediaValidationError('CANVAS_ERROR', 'Error al exportar canvas: ' + String(err)));
      }
    };
    img.onerror = () => reject(new MediaValidationError('INVALID_MIME', 'No se pudo decodificar la imagen.'));
    img.src = url;
  });
}