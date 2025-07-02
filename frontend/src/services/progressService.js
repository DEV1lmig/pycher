import { apiClient } from './api';

// --- Course Enrollment & Progress ---
export const enrollInCourse = async (courseId) => {
  const response = await apiClient.post(`/api/v1/users/courses/${courseId}/enroll`);
  return response.data;
};

export const getMyEnrollments = async () => {
  const response = await apiClient.get(`/api/v1/users/me/enrollments`);
  return response.data;
};

export const updateLastAccessed = async (courseId, moduleId = null, lessonId = null) => {
  const payload = {};
  if (moduleId) payload.moduleId = moduleId;
  if (lessonId) payload.lessonId = lessonId;
  const response = await apiClient.post(`/api/v1/users/progress/last-accessed?course_id=${courseId}`, payload);
  return response.data;
};

export const getLastAccessed = async () => {
  const response = await apiClient.get(`/api/v1/users/progress/last-accessed`);
  return response.data;
};

export const getCourseProgressSummary = async (courseId) => {
  const response = await apiClient.get(`/api/v1/users/courses/${courseId}/progress-summary`);
  return response.data;
};

// --- Module Progress ---
export const startModule = async (moduleId) => {
  const response = await apiClient.post(`/api/v1/users/modules/${moduleId}/start`);
  return response.data;
};

export const getModuleProgress = async (moduleId) => {
  const response = await apiClient.get(`/api/v1/users/modules/${moduleId}/progress`);
  return response.data;
};

export const getCompletedExercisesCount = async () => {
  const response = await apiClient.get('/api/v1/users/me/completed-exercises-count');
  return response.data;
};

// --- Lesson Progress ---
export const startLesson = async (lessonId) => {
  const response = await apiClient.post(`/api/v1/users/lessons/${lessonId}/start`);
  return response.data;
};

export const getLessonProgress = async (lessonId) => {
  const response = await apiClient.get(`/api/v1/users/lessons/${lessonId}/progress`);
  console.log('Lesson progress response:', response);
  return response.data;
};

// --- Exercise Submission ---
export const submitExercise = async (exerciseId, submittedCode, userInputData) => {
  const payload = {
    submitted_code: submittedCode,
    input_data: userInputData // Add this line
  };
  const response = await apiClient.post(`/api/v1/users/exercises/${exerciseId}/submit`, payload);
  return response.data;
};

// --- Exam Handling ---
export const getCourseExam = async (courseId) => {
  const response = await apiClient.get(`/api/v1/users/courses/${courseId}/exam`);
  return response.data;
};

/**
 * Gets the user's current, persistent exam exercise for a course.
 * If the user fails 5 times, a new one will be assigned.
 * @param {number} courseId The ID of the course.
 * @returns {Promise<Object>} The exam exercise object.
 */
export const getCurrentCourseExam = async (courseId) => {
  const response = await apiClient.get(`/api/v1/users/me/courses/${courseId}/current-exam`);
  return response.data;
};

export const startExamAttempt = async (examId) => {
  const response = await apiClient.post(`/api/v1/users/exams/${examId}/start-attempt`);
  return response.data;
};

export const submitExamAttempt = async (attemptId, answers) => {
  // answers should be in the format: [{ question_id: 1, answer: "A" }, ...]
  const payload = { answers };
  const response = await apiClient.post(`/api/v1/users/exam-attempts/${attemptId}/submit`, payload);
  return response.data;
};

export const getUserExamAttempts = async (examId) => {
  const response = await apiClient.get(`/api/v1/users/exams/${examId}/attempts`);
  return response.data;
};

/**
 * Fetch batch progress for multiple modules.
 * @param {number[]} moduleIds
 * @returns {Promise<Object>} Map of moduleId to progress object (including is_unlocked)
 */
export const getBatchModuleProgress = async (moduleIds) => {
  const response = await apiClient.post(`/api/v1/users/modules/progress/batch`, {
    module_ids: moduleIds,
  });
  return response.data.progress;
};

export const getBatchLessonProgress = async (lessonIds) => {
  const response = await apiClient.post(`/api/v1/users/lessons/progress/batch`, {
    lesson_ids: lessonIds,
  });
  return response.data.progress;
};

const progressService = {
  enrollInCourse,
  getMyEnrollments,
  updateLastAccessed,
  getLastAccessed,
  getCourseProgressSummary,
  startModule,
  getModuleProgress,
  startLesson,
  getLessonProgress,
  submitExercise,
  getCourseExam,
  getCurrentCourseExam,
  startExamAttempt,
  submitExamAttempt,
  getUserExamAttempts,
  getBatchModuleProgress,
  getBatchLessonProgress,
  getCompletedExercisesCount,
};

export default progressService;
