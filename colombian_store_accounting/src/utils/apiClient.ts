import axios, { AxiosError, AxiosInstance } from 'axios';
import { API_BASE_URL } from '../constants/api';

const API_TIMEOUT = parseInt((import.meta as any).env?.VITE_API_TIMEOUT || '30000', 10);
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // ms

interface ApiErrorResponse {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

class ApiClientError extends Error {
  constructor(
    public statusCode: number,
    public originalError: AxiosError,
    message: string
  ) {
    super(message);
    this.name = 'ApiClientError';
  }
}

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Add JWT access token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('[API] Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor: Handle 401 with token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;
    
    if (!originalRequest) {
      console.error('[API] No original request in error:', error);
      return Promise.reject(error);
    }

    // Handle 401 Unauthorized with token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const { data } = await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          {},
          { withCredentials: true, timeout: API_TIMEOUT }
        );
        
        if (!data?.accessToken) {
          throw new Error('No access token in refresh response');
        }
        
        localStorage.setItem('accessToken', data.accessToken);
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${data.accessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        console.error('[API] Token refresh failed:', refreshError);
        localStorage.removeItem('accessToken');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle network errors
    if (!error.response) {
      console.error('[API] Network error:', error.message);
      return Promise.reject(
        new ApiClientError(0, error, `Network error: ${error.message}`)
      );
    }

    // Handle server errors
    const errorData = error.response.data as ApiErrorResponse;
    const errorMessage = errorData?.message || error.message || 'Unknown API error';
    console.error(`[API] Error ${error.response.status}:`, errorMessage);
    
    return Promise.reject(
      new ApiClientError(error.response.status, error, errorMessage)
    );
  }
);

export { apiClient as default, ApiClientError };
export type { ApiErrorResponse };
