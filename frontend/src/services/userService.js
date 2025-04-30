import { apiClient } from './api';

export const registerUser = async (userData) => {

  const payload = {
    username: userData.username,
    email: userData.email,
    password: userData.password,
    first_name: userData.firstName,
    last_name: userData.lastName,
    // ...add any other fields you need
  };

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

export const logoutUser = () => {
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
