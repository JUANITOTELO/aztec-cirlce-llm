import { describe, it, expect } from 'vitest';
import { validateMediaFile, sanitizeFileName } from '../engine/mediaValidation';

describe('Media File Validation and Sanitization', () => {
  it('sanitizes malicious file names preventing path traversal', () => {
    const raw = '../../../etc/passwd.png';
    const safe = sanitizeFileName(raw);
    expect(safe).not.toContain('..');
    expect(safe).not.toContain('/');
    expect(safe).toBe('passwd.png');
  });

  it('rejects unapproved MIME types and extensions', () => {
    const mockFile = new File(['fake content'], 'malware.exe', { type: 'application/x-msdownload' });
    const errors = validateMediaFile(mockFile);
    expect(errors.length).toBeGreaterThan(0);
    expect(errors[0].field).toBe('file');
  });

  it('accepts valid JPEG files within size limits', () => {
    const mockFile = new File([new Uint8Array(1024)], 'photo.jpg', { type: 'image/jpeg' });
    const errors = validateMediaFile(mockFile);
    expect(errors.length).toBe(0);
  });
});
