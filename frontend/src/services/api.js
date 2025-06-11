// filepath: /home/dev1mig/Documents/projects/pycher/frontend/src/services/api.js
import axios from 'axios';
import { QueryClient } from '@tanstack/react-query';
import { router } from '@/router'; // Adjust path as needed

// Create API client with base URL
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add authentication interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle 401 and 403 errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      // Don't call logoutUser() if this IS the logout endpoint to prevent infinite loop
      if (!error.config.url.includes('/logout')) {
        // Clear token immediately
        localStorage.removeItem('token');

        // Navigate to login - use window.location to avoid router import issues
        router.navigate({ to: '/login' });
      }
    }
    return Promise.reject(error);
  }
);

// Configure QueryClient with defaults
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
