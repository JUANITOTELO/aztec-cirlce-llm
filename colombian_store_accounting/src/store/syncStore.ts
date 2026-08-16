import { create } from 'zustand';

type SyncStatus = 'online' | 'offline' | 'syncing' | 'error';

interface SyncState {
  status: SyncStatus;
  queueSize: number;
  setStatus: (status: SyncStatus) => void;
  setQueueSize: (size: number) => void;
}

export const useSyncStore = create<SyncState>((set) => ({
  status: navigator.onLine ? 'online' : 'offline',
  queueSize: 0,
  setStatus: (status) => set({ status }),
  setQueueSize: (size) => set({ queueSize: size }),
}));
