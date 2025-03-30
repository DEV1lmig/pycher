// filepath: /home/dev1mig/Documents/projects/pycher/frontend/src/services/api.js
import axios from 'axios';
import { QueryClient } from '@tanstack/react-query';

// Create API client with base URL
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

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
