// API Configuration
const env = (import.meta as any).env || {};
const isDevelopment = env.MODE === 'development';
const isProduction = env.MODE === 'production';

export const API_BASE_URL = env.VITE_API_BASE_URL || (
  isDevelopment ? 'http://127.0.0.1:8000/api' : '/api'
);

export const API_TIMEOUT = parseInt(env.VITE_API_TIMEOUT || '30000', 10);

export const API_CONFIG = {
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  retryAttempts: 3,
  retryDelay: 1000,
  enableLogging: isDevelopment,
} as const;

// Validate API configuration on startup
export function validateApiConfig(): void {
  if (!API_BASE_URL) {
    console.warn('[API] API_BASE_URL not configured, using default');
  }
  if (isProduction && API_BASE_URL.includes('localhost')) {
    console.error('[API] Production build using localhost API - this will fail!');
  }
}
