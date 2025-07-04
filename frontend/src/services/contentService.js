import { apiClient } from './api';

// Modules
export const getAllModules = async () => {
  const response = await apiClient.get('/api/v1/content/modules');
  return response.data;
};

export const getModuleById = async (moduleId) => {
  const response = await apiClient.get(`/api/v1/content/modules/${moduleId}`);
  return response.data;
};

export const getLessonsByModuleId = async (moduleId) => {
  const response = await apiClient.get(`/api/v1/content/modules/${moduleId}/lessons`);
  return response.data;
};

export const getLessonById = async (lessonId) => {
  const response = await apiClient.get(`/api/v1/content/lessons/${lessonId}`);
 return response.data;
};

// Exercises
export const getExercisesByLessonId = async (lessonId) => {
  const response = await apiClient.get(`/api/v1/content/lessons/${lessonId}/exercises`);
  return response.data;
};

export const getExerciseById = async (exerciseId) => {
  const response = await apiClient.get(`/api/v1/content/exercises/${exerciseId}`);
  return response.data;
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

export const downloadUserManual = async (filename) => {
  try {
    // Request the PDF file from the content-service as a binary large object (blob)
    const response = await apiClient.get(`/api/v1/content/pdf/${filename}`, {
      responseType: 'blob',
    });

    // Create a URL for the blob object
    const url = window.URL.createObjectURL(new Blob([response.data]));

    // Create a temporary anchor element to trigger the download
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename); // Set the desired filename

    // Append to the document, click, and then remove
    document.body.appendChild(link);
    link.click();
    link.remove();

    // Clean up the blob URL
    window.URL.revokeObjectURL(url);

    return { success: true, filename };
  } catch (error) {
    console.error("Error downloading PDF:", error);
    // Re-throw the error to be handled by the calling component
    throw new Error(error.response?.data?.detail || "Failed to download the user manual.");
  }
};

export const getCourseExamExercises = async (courseId) => {
    const response = await apiClient.get(`/api/v1/content/courses/${courseId}/exam-exercises`);
    return response.data;
}

export const getRandomCourseExam = async (courseId) => {
    const response = await apiClient.get(`/api/v1/content/courses/${courseId}/exam-random`);
    return response.data;
}
