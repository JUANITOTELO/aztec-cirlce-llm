import { SavedPoseRecord, SavedThemeRecord } from '../types/dummy13';

const DB_NAME = 'Dummy13_Studio_DB';
const DB_VERSION = 1;

const STORE_POSES = 'poses';
const STORE_THEMES = 'themes';
const STORE_SETTINGS = 'settings';

class IndexedDBService {
  private dbPromise: Promise<IDBDatabase> | null = null;

  private openDB(): Promise<IDBDatabase> {
    if (this.dbPromise) return this.dbPromise;

    this.dbPromise = new Promise<IDBDatabase>((resolve, reject) => {
      if (!window.indexedDB) {
        reject(new Error('IndexedDB is not supported in this browser.'));
        return;
      }

      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        if (!db.objectStoreNames.contains(STORE_POSES)) {
          const poseStore = db.createObjectStore(STORE_POSES, { keyPath: 'id' });
          poseStore.createIndex('timestamp', 'timestamp', { unique: false });
          poseStore.createIndex('name', 'name', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORE_THEMES)) {
          const themeStore = db.createObjectStore(STORE_THEMES, { keyPath: 'id' });
          themeStore.createIndex('createdAt', 'createdAt', { unique: false });
        }

        if (!db.objectStoreNames.contains(STORE_SETTINGS)) {
          db.createObjectStore(STORE_SETTINGS, { keyPath: 'key' });
        }
      };

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => {
        this.dbPromise = null;
        reject(request.error);
      };
    });

    return this.dbPromise;
  }

  // POSES CRUD
  async getAllPoses(): Promise<SavedPoseRecord[]> {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_POSES, 'readonly');
      const store = tx.objectStore(STORE_POSES);
      const request = store.getAll();
      request.onsuccess = () => {
        const results: SavedPoseRecord[] = request.result || [];
        results.sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
        resolve(results);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async savePose(pose: SavedPoseRecord): Promise<void> {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_POSES, 'readwrite');
      const store = tx.objectStore(STORE_POSES);
      const request = store.put(pose);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getPoseById(id: string): Promise<SavedPoseRecord | null> {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_POSES, 'readonly');
      const store = tx.objectStore(STORE_POSES);
      const request = store.get(id);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  }

  async deletePose(id: string): Promise<void> {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_POSES, 'readwrite');
      const store = tx.objectStore(STORE_POSES);
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  // THEMES CRUD
  async getAllThemes(): Promise<SavedThemeRecord[]> {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_THEMES, 'readonly');
      const store = tx.objectStore(STORE_THEMES);
      const request = store.getAll();
      request.onsuccess = () => resolve(request.result || []);
      request.onerror = () => reject(request.error);
    });
  }

  async saveTheme(theme: SavedThemeRecord): Promise<void> {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_THEMES, 'readwrite');
      const store = tx.objectStore(STORE_THEMES);
      const request = store.put(theme);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async deleteTheme(id: string): Promise<void> {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_THEMES, 'readwrite');
      const store = tx.objectStore(STORE_THEMES);
      const request = store.delete(id);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  // SETTINGS & AUTO-SAVE SESSION
  async setSetting<T = any>(key: string, value: T): Promise<void> {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_SETTINGS, 'readwrite');
      const store = tx.objectStore(STORE_SETTINGS);
      const request = store.put({ key, value, updatedAt: Date.now() });
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getSetting<T = any>(key: string): Promise<T | null> {
    const db = await this.openDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_SETTINGS, 'readonly');
      const store = tx.objectStore(STORE_SETTINGS);
      const request = store.get(key);
      request.onsuccess = () => {
        if (request.result && request.result.value !== undefined) {
          resolve(request.result.value);
        } else {
          resolve(null);
        }
      };
      request.onerror = () => reject(request.error);
    });
  }

  // BACKUP & RESTORE
  async exportAllData(): Promise<string> {
    const poses = await this.getAllPoses();
    const themes = await this.getAllThemes();
    const payload = {
      version: 1,
      exportedAt: Date.now(),
      poses,
      themes
    };
    return JSON.stringify(payload, null, 2);
  }

  async importAllData(jsonData: string): Promise<{ posesCount: number; themesCount: number }> {
    const parsed = JSON.parse(jsonData);
    let posesCount = 0;
    let themesCount = 0;

    if (Array.isArray(parsed.poses)) {
      for (const pose of parsed.poses) {
        if (pose.id && pose.joints) {
          await this.savePose(pose);
          posesCount++;
        }
      }
    }

    if (Array.isArray(parsed.themes)) {
      for (const theme of parsed.themes) {
        if (theme.id && theme.name) {
          await this.saveTheme(theme);
          themesCount++;
        }
      }
    }

    return { posesCount, themesCount };
  }
}

export const dbService = new IndexedDBService();
