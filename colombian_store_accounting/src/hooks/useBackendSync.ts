import { useState, useEffect, useCallback } from 'react';
import { BackendSyncEngine, BackendSyncState } from '../engine/backendSyncEngine';
import { db } from '../db/dexie';

export interface UseBackendSyncReturn {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncedAt: string | null;
  triggerSync: () => Promise<void>;
}

export function useBackendSync(
  onHydrate?: (data: BackendSyncState) => void
): UseBackendSyncReturn {
  const [isOnline, setIsOnline] = useState<boolean>(false);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);

  const triggerSync = useCallback(async () => {
    setIsSyncing(true);
    try {
      const data = await BackendSyncEngine.fetchAllData();
      if (data) {
        setIsOnline(true);
        setLastSyncedAt(new Date().toLocaleTimeString('es-CO'));

        // Populate Dexie IndexedDB with backend database records
        if (data.variants?.length) await db.productVariants.bulkPut(data.variants);
        if (data.images?.length) await db.productImages.bulkPut(data.images);
        if (data.categories?.length) await db.categories.bulkPut(data.categories);

        if (onHydrate) {
          onHydrate(data);
        }
      } else {
        setIsOnline(false);
      }
    } catch (err) {
      console.warn('[useBackendSync] Sync attempt failed:', err);
      setIsOnline(false);
    } finally {
      setIsSyncing(false);
    }
  }, [onHydrate]);

  useEffect(() => {
    triggerSync();
    const interval = setInterval(() => {
      BackendSyncEngine.checkHealth().then(setIsOnline);
    }, 15000);

    return () => clearInterval(interval);
  }, [triggerSync]);

  return {
    isOnline,
    isSyncing,
    lastSyncedAt,
    triggerSync,
  };
}
