import { apiClient } from './api';

/**
 * Helper function to download user manual with modal notifications
 * This function integrates with the useDownloadNotification hook
 * 
 * @param {string} filename - The filename to download
 * @param {Object} notificationHook - The useDownloadNotification hook object
 * @returns {Promise<Object>} Download result
 */
export const downloadUserManualWithNotification = async (filename, notificationHook) => {
  if (!notificationHook) {
    throw new Error('notificationHook is required. Please provide the useDownloadNotification hook.');
  }

  const { showSuccess, showError } = notificationHook;

  return downloadUserManual(filename, {
    onSuccess: (filename, message) => {
      showSuccess(filename, message);
    },
    onError: (filename, message) => {
      showError(filename, message);
    },
    useNotifications: true
  });
};

// Modules
export const getAllModules = async () => {
  const response = await apiClient.get('/api/v1/content/modules');
  return response.data;
};

export const getModuleById = async (moduleId) => {
  try {
    const response = await apiClient.get(`/api/v1/content/modules/${moduleId}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching module by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch module.");
  }
};

export const getLessonsByModuleId = async (moduleId) => {
  const response = await apiClient.get(`/api/v1/content/modules/${moduleId}/lessons`);
  return response.data;
};

export const getLessonById = async (lessonId) => {
  try {
    const response = await apiClient.get(`/api/v1/content/lessons/${lessonId}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching lesson by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch lesson.");
  }
};

// Exercises
export const getExercisesByLessonId = async (lessonId) => {
  const response = await apiClient.get(`/api/v1/content/lessons/${lessonId}/exercises`);
  return response.data;
};

export const getExerciseById = async (exerciseId) => {
  try {
    const response = await apiClient.get(`/api/v1/content/exercises/${exerciseId}`);
    return response.data;
  } catch (error) {
    console.error("Error fetching exercise by ID:", error);
    throw new Error(error.response?.data?.detail || "Failed to fetch exercise.");
  }
};

// Courses
export const getAllCourses = async () => {
  const response = await apiClient.get('/api/v1/content/courses');
  return response.data;
};

export const getCourseById = async (courseId) => {
  const response = await apiClient.get(`/api/v1/content/courses/${courseId}`);
  return response.data;
};

export const getModulesByCourseId = async (courseId) => {
  const response = await apiClient.get(`/api/v1/content/courses/${courseId}/modules`);
  return response.data;
};

export const getNextLessonInfo = async (lessonId) => {
  if (!lessonId) return null;
  try {
    const response = await apiClient.get(`/api/v1/content/lessons/${lessonId}/next`);
    return response.data; // This will be the next lesson info object or null
  } catch (error) {
    return null;
  }
};

export const downloadUserManual = async (filename, options = {}) => {
  const { onSuccess, onError, useNotifications = false } = options;
  
  try {
    // Request the PDF file from the content-service as a binary large object (blob)
    const response = await apiClient.get(`/api/v1/content/pdf/${filename}`, {
      responseType: 'blob',
    });

    // Create a URL for the blob object
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
    link.setAttribute('download', filename); // Set the desired filename
    link.style.display = 'none'; // Hide the link
    link.target = '_blank'; // Ensure it opens in new tab if clicked

    // Append to the document, click, and then remove
    document.body.appendChild(link);
    link.click();
    link.remove();

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
    console.error("Error downloading PDF:", error);
    
    // Enhanced error handling with better user feedback
    let errorMessage = "Error al descargar el manual de usuario. Por favor, inténtalo de nuevo.";
    
    if (error.response) {
      // Server responded with error status
      if (error.response.status === 404) {
        errorMessage = "El archivo solicitado no se encontró. Por favor, contacta al soporte.";
      } else if (error.response.status === 403) {
        errorMessage = "No tienes permisos para descargar este archivo.";
      } else if (error.response.status >= 500) {
        errorMessage = "Error del servidor. Por favor, inténtalo más tarde.";
      } else if (error.response.data?.detail) {
        errorMessage = error.response.data.detail;
      }
    } else if (error.request) {
      // Network error
      errorMessage = "Error de conexión. Verifica tu conexión a internet e inténtalo de nuevo.";
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

export const getCourseExamExercises = async (courseId) => {
    const response = await apiClient.get(`/api/v1/content/courses/${courseId}/exam-exercises`);
    return response.data;
}

export const getRandomCourseExam = async (courseId) => {
    try {
        const response = await apiClient.get(`/api/v1/content/courses/${courseId}/exam-random`);
        return response.data;
    } catch (error) {
        console.error("Error fetching random course exam:", error);
        throw new Error(error.response?.data?.detail || "Failed to fetch random exam.");
    }
}
