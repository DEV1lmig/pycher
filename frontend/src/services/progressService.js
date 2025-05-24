import api from './api';

const API_URL = import.meta.env.VITE_API_URL;

// --- Course Enrollment & Progress ---
export const enrollInCourse = async (courseId) => {
  const response = await api.post(`/users/courses/${courseId}/enroll`);
  return response.data;
};

export const getMyEnrollments = async () => {
  const response = await api.get(`/users/me/enrollments`);
  return response.data;
};

export const updateLastAccessed = async (courseId, moduleId = null, lessonId = null) => {
  const payload = {};
  if (moduleId) payload.moduleId = moduleId;
  if (lessonId) payload.lessonId = lessonId;
  const response = await api.post(`/users/progress/last-accessed?course_id=${courseId}`, payload);
  return response.data;
};

export const getLastAccessed = async () => {
  const response = await api.get(`/users/progress/last-accessed`);
  return response.data;
};

export const getCourseProgressSummary = async (courseId) => {
  const response = await api.get(`/users/courses/${courseId}/progress-summary`);
  return response.data;
};

// --- Module Progress ---
export const startModule = async (moduleId) => {
  const response = await api.post(`/users/modules/${moduleId}/start`);
  return response.data;
};

export const completeModule = async (moduleId) => {
  const response = await api.post(`/users/modules/${moduleId}/complete`);
  return response.data;
};

export const getModuleProgress = async (moduleId) => {
  const response = await api.get(`/users/modules/${moduleId}/progress`);
  return response.data;
};

// --- Lesson Progress ---
export const startLesson = async (lessonId) => {
  const response = await api.post(`/users/lessons/${lessonId}/start`);
  return response.data;
};

export const completeLesson = async (lessonId) => {
  const response = await api.post(`/users/lessons/${lessonId}/complete`);
  return response.data;
};

export const getLessonProgress = async (lessonId) => {
  const response = await api.get(`/users/lessons/${lessonId}/progress`);
  return response.data;
};

// --- Exercise Submission ---
export const submitExercise = async (exerciseId, submittedCode, isCorrect, output = null) => {
  const payload = { submitted_code: submittedCode, is_correct: isCorrect, output };
  const response = await api.post(`/users/exercises/${exerciseId}/submit`, payload);
  return response.data;
};

// --- Exam Handling ---
export const getCourseExam = async (courseId) => {
  const response = await api.get(`/users/courses/${courseId}/exam`);
  return response.data;
};

export const startExamAttempt = async (examId) => {
  const response = await api.post(`/users/exams/${examId}/start-attempt`);
  return response.data;
};

export const submitExamAttempt = async (attemptId, answers) => {
  // answers should be in the format: [{ question_id: 1, answer: "A" }, ...]
  const payload = { answers };
  const response = await api.post(`/users/exam-attempts/${attemptId}/submit`, payload);
  return response.data;
};

export const getUserExamAttempts = async (examId) => {
  const response = await api.get(`/users/exams/${examId}/attempts`);
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
