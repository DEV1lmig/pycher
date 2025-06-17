import { apiClient } from './api';

const API_URL = "/api/v1/users"; // Adjust as needed

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

  // Always clear the token first, regardless of API call success
  localStorage.removeItem('token');

  // Only try to call the logout endpoint if we have a token
  if (token) {
    try {
      await apiClient.post(`${API_URL}/logout`, {}, {
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
  const response = await apiClient.get(`${API_URL}/progress/${userId}/${moduleId}`);
  return response.data;
};

export const updateLessonProgress = async (progressData) => {
  const response = await apiClient.post(`${API_URL}/progress`, progressData);
  return response.data;
};

export const getUserProfile = async () => {
  const response = await apiClient.get(`${API_URL}/me`);
  return response.data;
};

export const updateUserProfile = async (userData) => {
  const response = await apiClient.put(`${API_URL}/me`, userData);
  return response.data;
};

export const enrollInCourse = async (courseId) => {
  const response = await apiClient.post(`${API_URL}/courses/${courseId}/enroll`);
  return response.data;
};

export const getUserEnrollments = async () => {
  // OLD URL: const response = await apiClient.get('/api/v1/users/users/me/enrollments');
  const response = await apiClient.get(`${API_URL}/me/enrollments`); // CORRECTED URL
  return response.data;
};

export const getCourseProgressSummary = async (courseId) => {
  const response = await apiClient.get(`${API_URL}/courses/${courseId}/progress-summary`);
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
    console.error("Error checking course access:", error);
    // Fallback: if there's an error, deny access by default or handle as appropriate
    return { hasAccess: false, reason: "Error al verificar el acceso al curso." };
  }
}; // Make sure this function is properly closed if it was the last one

export const unenrollFromCourse = async (courseId) => {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error("User not authenticated. Cannot unenroll.");
  }
  const response = await apiClient.delete(`${API_URL}/courses/${courseId}/unenroll`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response;
};

// --- New Progress Related Service Functions ---

/**
 * Marks a lesson as started for the current user.
 * @param {number} lessonId - The ID of the lesson to start.
 * @returns {Promise<object>} The response data from the API.
 */
export const startLesson = async (lessonId) => {
  const response = await apiClient.post(`${API_URL}/lessons/${lessonId}/start`);
  return response.data; // Assuming backend returns UserLessonProgress or similar
};

/**
 * Submits an exercise attempt for the current user.
 * @param {number} exerciseId - The ID of the exercise.
 * @param {string} submittedCode - The code submitted by the user.
 * @returns {Promise<object>} The submission result from the API.
 */
export const submitExerciseAttempt = async (exerciseId, submittedCode) => {
  // The backend's complete_exercise service expects:
  // user_id (from token), exercise_id, submitted_code, is_correct, output
  // The frontend will send submitted_code. The backend should evaluate it.
  // Let's assume the endpoint /submit handles this and then calls complete_exercise.
  const response = await apiClient.post(`${API_URL}/exercises/${exerciseId}/submit`, {
    submitted_code: submittedCode,
    // is_correct and output will be determined by the backend after evaluation
  });
  return response.data; // Should return the UserExerciseSubmission and potentially updated lesson status
};

/**
 * Gets detailed progress for a specific lesson for the current user.
 * This includes the lesson's completion status and the status of its exercises.
 * @param {number} lessonId - The ID of the lesson.
 * @returns {Promise<object>} Detailed progress for the lesson.
 */
export const getLessonDetailedProgress = async (lessonId) => {
  const response = await apiClient.get(`/api/v1/users/lessons/${lessonId}/progress`);
  return response.data; // Expects format like the example in the plan
};

export const downloadProgressReport = async () => {
  try {
    const token = localStorage.getItem('token');
    if (!token) {
      // Handle case where user is not authenticated or token is missing
      // You might want to redirect to login or show an error
      console.error("No token found. User might not be authenticated.");
      throw new Error("Authentication required to download the report.");
    }

    const response = await apiClient.get('/api/v1/users/me/progress/report/pdf', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
      responseType: 'blob', // Important for handling file downloads
    });

    // Extract filename from content-disposition header if available, otherwise fallback
    const contentDisposition = response.headers['content-disposition'];
    let filename = 'Pycher_Progress_Report.pdf'; // Default filename
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch && filenameMatch.length > 1) {
        filename = filenameMatch[1];
      }
    }

    // Create a URL for the blob
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename); // Use the extracted or default filename
    document.body.appendChild(link);
    link.click();

    // Clean up by removing the link and revoking the object URL
    link.parentNode.removeChild(link);
    window.URL.revokeObjectURL(url);

    return { success: true, filename };
  } catch (error) {
    console.error('Error downloading progress report:', error);
    // Try to parse error response if it's a JSON blob (some errors might be returned as JSON)
    if (error.response && error.response.data instanceof Blob && error.response.data.type === "application/json") {
      const errorText = await error.response.data.text();
      const errorJson = JSON.parse(errorText);
      throw new Error(errorJson.detail || 'Failed to download progress report.');
    }
    throw new Error(error.message || 'Failed to download progress report.');
  }
};

/**
 * Checks if the next course is unlocked for the user.
 * @param {number} currentCourseId - The current course's ID.
 * @returns {Promise<{unlocked: boolean, nextCourseId: number|null, reason: string|null}>}
 */
export const isNextCourseUnlocked = async (currentCourseId) => {
  // Get all enrollments for the user
  const enrollments = await getUserEnrollments();

  // Find the current course enrollment and check if it's completed
  const currentEnrollment = enrollments.find(e => e.course_id === currentCourseId);
  if (!currentEnrollment || !currentEnrollment.is_completed) {
    return {
      unlocked: false,
      nextCourseId: null,
      reason: "Debes completar el curso actual para desbloquear el siguiente."
    };
  }

  // Find the next course (assuming sequential IDs)
  const nextCourseId = currentCourseId + 1;
  const nextEnrollment = enrollments.find(e => e.course_id === nextCourseId);

  // If already enrolled in next course, it's unlocked
  if (nextEnrollment) {
    return {
      unlocked: true,
      nextCourseId,
      reason: null
    };
  }

  // Otherwise, allow unlock if current is completed
  return {
    unlocked: true,
    nextCourseId,
    reason: null
  };
};
