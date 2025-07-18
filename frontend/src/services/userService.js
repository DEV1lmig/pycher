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

/**
 * Helper function to download progress report with modal notifications
 * This function integrates with the useDownloadNotification hook
 * 
 * @param {Object} notificationHook - The useDownloadNotification hook object
 * @returns {Promise<Object>} Download result
 */
export const downloadProgressReportWithNotification = async (notificationHook) => {
  if (!notificationHook) {
    throw new Error('notificationHook is required. Please provide the useDownloadNotification hook.');
  }

  const { showSuccess, showError } = notificationHook;

  return downloadProgressReport({
    onSuccess: (filename, message) => {
      showSuccess(filename, message);
    },
    onError: (filename, message) => {
      showError(filename, message);
    },
    useNotifications: true
  });
};

export const downloadProgressReport = async (options = {}) => {
  const { onSuccess, onError, useNotifications = false } = options;
  
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error("Authentication required to download the report.");
    }
    
    const response = await apiClient.get('/api/v1/users/me/progress/report/pdf', {
      headers: { Authorization: `Bearer ${token}` },
      responseType: 'blob',
    });
    
    // Extract filename from response headers
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'Pycher_Progress_Report.pdf';
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch && filenameMatch.length > 1) {
        filename = filenameMatch[1];
      }
    }
    
    // Create download link and open in new tab
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    
    // Open PDF in new tab without switching focus (background tab)
    const newTab = window.open();
    if (newTab) {
      newTab.location.href = url;
      // Immediately return focus to current window
      window.focus();
    }
    
    // Also create a download link as fallback and for accessibility
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    link.style.display = 'none'; // Hide the link
    link.target = '_blank'; // Ensure it opens in new tab if clicked
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    
    // Clean up the blob URL after a delay to ensure the new tab loads
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
    }, 1000);
    
    const result = { success: true, filename };

    // Call success callback if provided (for new modal system)
    if (onSuccess && typeof onSuccess === 'function') {
      onSuccess(filename, `${filename} se ha descargado exitosamente`);
    }

    return result;
  } catch (error) {
    console.error("Error downloading progress report:", error);
    
    // Enhanced error handling with better user feedback
    let errorMessage = "Error al descargar el reporte de progreso. Por favor, inténtalo de nuevo.";
    let filename = 'Pycher_Progress_Report.pdf'; // Default filename for error display
    
    if (error.response) {
      // Handle blob error responses (JSON in blob format)
      if (error.response.data instanceof Blob && error.response.data.type === "application/json") {
        try {
          const errorText = await error.response.data.text();
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorMessage;
        } catch (parseError) {
          console.error("Error parsing blob error response:", parseError);
        }
      }
      // Server responded with error status
      else if (error.response.status === 401) {
        errorMessage = "Sesión expirada. Por favor, inicia sesión nuevamente.";
      } else if (error.response.status === 403) {
        errorMessage = "No tienes permisos para descargar este reporte.";
      } else if (error.response.status === 404) {
        errorMessage = "El reporte solicitado no se encontró. Por favor, contacta al soporte.";
      } else if (error.response.status >= 500) {
        errorMessage = "Error del servidor. Por favor, inténtalo más tarde.";
      } else if (error.response.data?.detail) {
        errorMessage = error.response.data.detail;
      }
    } else if (error.request) {
      // Network error
      errorMessage = "Error de conexión. Verifica tu conexión a internet e inténtalo de nuevo.";
    } else if (error.message) {
      errorMessage = error.message;
    }

    // Call error callback if provided (for new modal system)
    if (onError && typeof onError === 'function') {
      onError(filename, errorMessage);
    }

    // For backward compatibility, still throw the error
    const enhancedError = new Error(errorMessage);
    enhancedError.originalError = error;
    enhancedError.filename = filename;
    throw enhancedError;
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
