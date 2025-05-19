import { apiClient } from './api';

export const registerUser = async (payload) => {

  const response = await apiClient.post('/api/v1/users/register', payload);
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

  localStorage.setItem('token', response.data.access_token);
  return response.data;
};

export const logoutUser = async () => {
  try {
    await apiClient.post('/api/v1/users/logout', {}, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`,
      },
    });
  } catch (e) {
    console.error('Logout failed:', e);
  }
  localStorage.removeItem('token');
};

export const getUserProgress = async (userId, moduleId) => {
  const response = await apiClient.get(`/api/v1/users/progress/${userId}/${moduleId}`);
  return response.data;
};

export const updateLessonProgress = async (progressData) => {
  const response = await apiClient.post('/api/v1/users/progress', progressData);
  return response.data;
};

export const getUserProfile = async () => {
  const response = await apiClient.get('/api/v1/users/me', {
    headers: {
      Authorization: `Bearer ${localStorage.getItem('token')}`,
    },
  });
  return response.data;
};
