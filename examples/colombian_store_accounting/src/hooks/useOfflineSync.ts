import { useEffect, useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, TransactionQueueItem } from '../db/dexie';
import apiClient from '../utils/apiClient';
import { useSyncStore } from '../store/syncStore';

/**
 * Hook to manage offline transaction queue and sync with the backend.
 */
export const useOfflineSync = () => {
  const transactionQueue = useLiveQuery(() => db.transactionQueue.toArray());
  const { setStatus, setQueueSize } = useSyncStore();
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const goOnline = () => setIsOnline(true);
    const goOffline = () => setIsOnline(false);

    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);

    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);

  useEffect(() => {
    setQueueSize(transactionQueue?.length ?? 0);

    if (isOnline && transactionQueue && transactionQueue.length > 0) {
      processQueue(transactionQueue);
    }
  }, [transactionQueue, isOnline, setQueueSize]);

  const processQueue = async (queue: TransactionQueueItem[]) => {
    setStatus('syncing');
    for (const item of queue) {
      try {
        await apiClient.post('/pos/sync', item.payload);
        await db.transactionQueue.delete(item.id!);
      } catch (error: any) {
        if (error.response?.status === 409) {
          // Conflict: transaction already exists, remove from queue
          console.warn('Transaction already synced, removing from queue:', item.id);
          await db.transactionQueue.delete(item.id!);
        } else {
          console.error('Failed to sync transaction:', item.id, error);
          setStatus('error');
          // Stop processing on first error to maintain order
          return;
        }
      }
    }
    setStatus(isOnline ? 'online' : 'offline');
  };
};
