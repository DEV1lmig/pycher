import { apiClient } from './api';

const API_URL = "/api/v1/users";

export async function updateUsername(newUsername) {
    const response = await apiClient.post(`${API_URL}/change-username`, {
        new_username: newUsername,
    });
    return response.data;
}

export async function updatePassword(currentPassword, newPassword) {
    const response = await apiClient.post(`${API_URL}/change-password`, {
        current_password: currentPassword,
        new_password: newPassword,
    });
    return response.data;
}

export const registerUser = async (payload) => {
  const response = await apiClient.post(`${API_URL}/register`, payload);
  return response.data;
};

export const loginUser = async (credentials) => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  const response = await apiClient.post(`${API_URL}/token`, formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  localStorage.setItem('token', response.data.access_token);
  return response.data;
};

export const logoutUser = async () => {
  const token = localStorage.getItem('token');
  localStorage.removeItem('token');
  if (token) {
    try {
      await apiClient.post(`${API_URL}/logout`, {}, {
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (e) {
      console.error('Server logout failed (but local logout succeeded):', e);
    }
  }
};

export const getUserProfile = async () => {
  const response = await apiClient.get(`${API_URL}/me`);
  return response.data;
};

export const updateUserProfile = async (userData) => {
  const response = await apiClient.put(`${API_URL}/me`, userData);
  return response.data;
};

export const unenrollFromCourse = async (courseId) => {
  const response = await apiClient.delete(`${API_URL}/courses/${courseId}/unenroll`);
  return response;
};

export const downloadProgressReport = async () => {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error("Authentication required to download the report.");
    }
    const response = await apiClient.get('/api/v1/users/me/progress/report/pdf', {
      headers: { Authorization: `Bearer ${token}` },
      responseType: 'blob',
    });
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'Pycher_Progress_Report.pdf';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch && filenameMatch.length > 1) {
        filename = filenameMatch[1];
      }
    }
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);
    return { success: true, filename };
  } catch (error) {
    if (error.response && error.response.data instanceof Blob && error.response.data.type === "application/json") {
      const errorText = await error.response.data.text();
      const errorJson = JSON.parse(errorText);
      throw new Error(errorJson.detail || 'Failed to download progress report.');
    }
    throw new Error(error.message || 'Failed to download progress report.');
  }
};

// --- REMOVED FUNCTIONS ---
// The following functions have been removed from userService.js to consolidate
// all progress-related logic into progressService.js.
// - getUserProgress
// - updateLessonProgress
// - enrollInCourse
// - getUserEnrollments
// - getCourseProgressSummary
// - checkCourseAccess (client-side logic, should be handled by hooks)
// - startLesson
// - submitExerciseAttempt
// - getLessonDetailedProgress
// - isNextCourseUnlocked (client-side logic, should be handled by hooks)
