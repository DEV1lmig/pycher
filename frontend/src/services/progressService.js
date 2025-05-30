import { apiClient } from './api';

const API_URL = import.meta.env.VITE_API_URL;

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

export const completeModule = async (moduleId) => {
  const response = await apiClient.post(`/api/v1/users/modules/${moduleId}/complete`);
  return response.data;
};

export const getModuleProgress = async (moduleId) => {
  const response = await apiClient.get(`/api/v1/users/modules/${moduleId}/progress`);
  return response.data;
};

// --- Lesson Progress ---
export const startLesson = async (lessonId) => {
  const response = await apiClient.post(`/api/v1/users/lessons/${lessonId}/start`);
  return response.data;
};

export const completeLesson = async (lessonId) => {
  const response = await apiClient.post(`/api/v1/users/lessons/${lessonId}/complete`);
  return response.data;
};

export const getLessonProgress = async (lessonId) => {
  const response = await apiClient.get(`/api/v1/users/lessons/${lessonId}/progress`);
  return response.data;
};

// --- Exercise Submission ---
export const submitExercise = async (exerciseId, submittedCode) => {
  const payload = { submitted_code: submittedCode };
  // This calls: http://localhost:8000/api/v1/users/exercises/{exerciseId}/submit
  // (Assuming apiClient is configured to point to the API Gateway at localhost:8000 and prefixes with /api/v1)
  const response = await apiClient.post(`/api/v1/users/exercises/${exerciseId}/submit`, payload);
  return response.data;
};

// --- Exam Handling ---
export const getCourseExam = async (courseId) => {
  const response = await apiClient.get(`/api/v1/users/courses/${courseId}/exam`);
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

const progressService = {
  enrollInCourse,
  getMyEnrollments,
  updateLastAccessed,
  getLastAccessed,
  getCourseProgressSummary,
  startModule,
  completeModule,
  getModuleProgress,
  startLesson,
  completeLesson,
  getLessonProgress,
  submitExercise,
  getCourseExam,
  startExamAttempt,
  submitExamAttempt,
  getUserExamAttempts,
};

export default progressService;
