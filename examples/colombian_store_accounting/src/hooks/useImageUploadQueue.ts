import { useState, useCallback } from 'react';
import { addTransactionToQueue } from '../db/dexie';
import { hasPermission } from '../types/permissions';
import { UserAccount } from '../types/store';

export interface UploadTask {
  id: string;
  file: File;
  status: 'queued' | 'uploading' | 'completed' | 'failed';
  error?: string;
}

export const useImageUploadQueue = (currentUser?: UserAccount) => {
  const [queue, setQueue] = useState<UploadTask[]>([]);

  const user = currentUser || {
    id: 'usr-admin',
    name: 'Admin',
    email: 'admin@pos.local',
    roleId: 'role-admin',
    role: 'admin',
    permissions: ['*'],
  };

  const addUpload = useCallback(async (file: File, productId: string) => {
    if (!hasPermission(user, 'products.manage_media')) throw new Error('Unauthorized');
    const taskId = crypto.randomUUID();
    setQueue((prev) => [...prev, { id: taskId, file, status: 'queued' }]);
    
    try {
      const buffer = await file.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
      const fileHash = Array.from(new Uint8Array(hashBuffer)).map((b) => b.toString(16).padStart(2, '0')).join('');
      
      await addTransactionToQueue('VARIANT_MUTATION', { type: 'IMAGE_UPLOAD', productId, fileHash, fileName: file.name });
      setQueue((prev) => prev.map((t) => (t.id === taskId ? { ...t, status: 'completed' } : t)));
    } catch (e) {
      setQueue((prev) => prev.map((t) => (t.id === taskId ? { ...t, status: 'failed', error: String(e) } : t)));
    }
  }, [user]);

  return { queue, addUpload };
};