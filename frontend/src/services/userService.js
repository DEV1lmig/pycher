import { apiClient } from './api';

// Authentication
export const registerUser = async (userData) => {
  const response = await apiClient.post('/api/v1/users/register', userData);
  return response.data;
};

export const loginUser = async (credentials) => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  const response = await apiClient.post('/api/v1/users/token', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  // Store token in local storage
  localStorage.setItem('token', response.data.access_token);
  return response.data;
};

export const logoutUser = () => {
  localStorage.removeItem('token');
};

// Progress tracking
export const getUserProgress = async (userId, moduleId) => {
  const response = await apiClient.get(`/api/v1/users/progress/${userId}/${moduleId}`);
  return response.data;
};

export const updateLessonProgress = async (progressData) => {
  const response = await apiClient.post('/api/v1/users/progress', progressData);
  return response.data;
};
