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
  const token = localStorage.getItem('token');

  // Always clear the token first, regardless of API call success
  localStorage.removeItem('token');

  // Only try to call the logout endpoint if we have a token
  if (token) {
    try {
      await apiClient.post('/api/v1/users/logout', {}, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
    } catch (e) {
      // Don't throw here - logout should always succeed locally
      console.error('Server logout failed (but local logout succeeded):', e);
    }
  }
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
  const response = await apiClient.get('/api/v1/users/me');
  return response.data;
};

export const updateUserProfile = async (userData) => {
  const response = await apiClient.put('/api/v1/users/me', userData);
  return response.data;
};

export const enrollInCourse = async (courseId) => {
  const response = await apiClient.post(`/api/v1/users/courses/${courseId}/enroll`);
  return response.data;
};

export const getUserEnrollments = async () => {
  const response = await apiClient.get('/api/v1/users/users/me/enrollments');
  return response.data;
};

export const getCourseProgressSummary = async (courseId) => {
  const response = await apiClient.get(`/api/v1/users/courses/${courseId}/progress-summary`);
  return response.data;
};

export const checkCourseAccess = async (courseId) => {
  try {
    const enrollments = await getUserEnrollments();
    const userProgress = enrollments.find(e => e.course_id === parseInt(courseId));

    // Basic course (ID 1) is always accessible
    if (courseId === 1 || courseId === "1") {
      return { hasAccess: true, reason: null };
    }

    // For other courses, check if previous course is completed
    const previousCourseId = courseId - 1;
    const previousCourseProgress = enrollments.find(e => e.course_id === previousCourseId);

    if (!previousCourseProgress || !previousCourseProgress.is_completed) {
      return {
        hasAccess: false,
        reason: `Debes completar el curso anterior primero.`
      };
    }

    return { hasAccess: true, reason: null };
  } catch (error) {
    console.error('Error checking course access:', error);
    return { hasAccess: false, reason: 'Error verificando acceso al curso' };
  }
};
