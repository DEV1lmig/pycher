import { useState, useEffect, useCallback } from 'react';
import { getLessonById, getExercisesByLessonId } from '@/services/contentService'; // Assuming these exist
import { startLesson, submitExerciseAttempt, getLessonDetailedProgress } from '@/services/userService';
import { toast } from 'react-hot-toast';

export function useLessonDetail(lessonId) {
  const [lesson, setLesson] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [lessonProgress, setLessonProgress] = useState(null); // Stores { is_completed, exercises_progress: [...] }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submittingExerciseId, setSubmittingExerciseId] = useState(null);

  const fetchData = useCallback(async () => {
    if (!lessonId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // Mark lesson as started (backend handles if already started)
      try {
        await startLesson(lessonId);
      } catch (startError) {
        // Non-critical if it fails because it was already started or user not enrolled
        // Critical errors (like 404 lesson) will be caught by subsequent calls.
        console.warn(`Attempt to start lesson ${lessonId} had an issue (might be okay):`, startError);
      }

      const [lessonData, exercisesData, progressData] = await Promise.all([
        getLessonById(lessonId),
        getExercisesByLessonId(lessonId),
        getLessonDetailedProgress(lessonId),
      ]);
      setLesson(lessonData);
      setExercises(Array.isArray(exercisesData) ? exercisesData : (exercisesData ? [exercisesData] : []));
      setLessonProgress(progressData);
    } catch (err) {
      console.error(`Error fetching lesson detail for lesson ${lessonId}:`, err);
      setError(err.response?.data?.detail || err.message || 'Failed to load lesson data.');
      toast.error(err.response?.data?.detail || 'Error al cargar la lección.');
      setLesson(null);
      setExercises([]);
      setLessonProgress(null);
    } finally {
      setLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleExerciseSubmit = async (exerciseId, submittedCode) => {
    setSubmittingExerciseId(exerciseId);
    try {
      const result = await submitExerciseAttempt(exerciseId, submittedCode);
      toast.success(result.is_correct ? `Ejercicio enviado correctamente!` : `Intento registrado. ¡Sigue intentando!`);
      // Refresh progress after submission
      const updatedProgressData = await getLessonDetailedProgress(lessonId);
      setLessonProgress(updatedProgressData);
      return result; // Contains UserExerciseSubmission
    } catch (err) {
      console.error(`Error submitting exercise ${exerciseId}:`, err);
      toast.error(err.response?.data?.detail || 'Error al enviar el ejercicio.');
      throw err; // Re-throw for component to handle if needed
    } finally {
      setSubmittingExerciseId(null);
    }
  };

  const isLessonCompleted = lessonProgress?.is_completed || false;
  const getExerciseProgress = (exerciseId) => {
    return lessonProgress?.exercises_progress?.find(ep => ep.exercise_id === exerciseId) || null;
  };

  return {
    lesson,
    exercises,
    lessonProgress,
    isLessonCompleted,
    getExerciseProgress,
    loading,
    error,
    submittingExerciseId,
    refreshData: fetchData,
    submitExercise: handleExerciseSubmit,
  };
}
