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

export const getCourseExamExercises = async (courseId) => {
    const response = await apiClient.get(`/api/v1/content/courses/${courseId}/exam-exercises`);
    return response.data;
}

export const getRandomCourseExam = async (courseId) => {
    const response = await apiClient.get(`/api/v1/content/courses/${courseId}/exam-random`);
    return response.data;
}
