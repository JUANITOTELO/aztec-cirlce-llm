import React, { useState, useRef } from 'react';
import { UploadCloud, AlertCircle, Loader2 } from 'lucide-react';
import { compressAndOptimizeImage, MediaValidationError } from '../../engine/imageOptimizer';

interface ImageDropZoneProps {
  onFilesSelected: (files: File[]) => void;
  isUploading: boolean;
  disabled?: boolean;
  accept?: string;
  maxFiles?: number;
}

export const ImageDropZone: React.FC<ImageDropZoneProps> = ({
  onFilesSelected,
  isUploading,
  disabled = false,
  accept = 'image/png,image/jpeg,image/webp',
  maxFiles = 5,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [dragError, setDragError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = async (fileList: FileList | null) => {
    if (!fileList || fileList.length === 0 || disabled || isUploading) return;
    setDragError(null);
    const files = Array.from(fileList);
    if (files.length > maxFiles) {
      setDragError(`Máximo permitido: ${maxFiles} imágenes por carga`);
      return;
    }
    try {
      for (const file of files) {
        await compressAndOptimizeImage(file);
      }
      onFilesSelected(files);
    } catch (err: any) {
      const message = err instanceof MediaValidationError ? err.message : 'Error al validar imagen';
      setDragError(message);
    }
  };

  return (
    <div className="w-full">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled && !isUploading) setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setIsDragOver(false);
          handleFiles(e.dataTransfer.files);
        }}
        onClick={() => !disabled && !isUploading && inputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
          isDragOver
            ? 'border-emerald-500 bg-emerald-500/10 scale-[1.01]'
            : 'border-slate-700 bg-slate-800/40 hover:border-slate-500 hover:bg-slate-800/70'
        } ${disabled || isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={accept}
          className="hidden"
          disabled={disabled || isUploading}
          onChange={(e) => {
            handleFiles(e.target.files);
            e.target.value = '';
          }}
        />
        {isUploading ? (
          <div className="flex flex-col items-center gap-2 text-emerald-400 py-2">
            <Loader2 className="w-8 h-8 animate-spin" />
            <p className="text-xs font-semibold">Optimizando y subiendo imágenes...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center text-center gap-2">
            <div className="w-12 h-12 rounded-full bg-slate-700/60 flex items-center justify-center text-slate-300">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm font-medium text-slate-200">
                Arrastra imágenes aquí o <span className="text-emerald-400 underline">explora</span>
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">PNG, JPG, WEBP hasta 3MB</p>
            </div>
          </div>
        )}
      </div>
      {dragError && (
        <div className="mt-2 flex items-center gap-1.5 text-xs text-rose-400 bg-rose-950/40 px-3 py-1.5 rounded-lg border border-rose-800/50">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{dragError}</span>
        </div>
      )}
    </div>
  );
};
