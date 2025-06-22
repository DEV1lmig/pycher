import { useState, useEffect, useCallback, useRef } from 'react';
import { getLessonById, getExercisesByLessonId } from '@/services/contentService';
import { startLesson, getLessonProgress, submitExercise as submitExerciseApi } from '@/services/progressService';
import { toast } from 'react-hot-toast';

export function useLessonDetail(lessonId) {
  const [lesson, setLesson] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [lessonProgress, setLessonProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submittingExerciseId, setSubmittingExerciseId] = useState(null);

  const startLessonCalled = useRef(false);

  // NEW: A targeted function to only refetch progress data.
  // This avoids triggering the main page loading state.
  const refetchProgress = useCallback(async () => {
    if (!lessonId) return;
    try {
      const progressData = await getLessonProgress(lessonId);
      setLessonProgress(progressData);
    } catch (err) {
      toast.error('No se pudo actualizar el progreso de la lección.');
    }
  }, [lessonId]);


  const fetchLessonData = useCallback(async () => {
    if (!lessonId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    // --- FIX: Prevent startLesson from being called twice ---
    // Only call startLesson if it hasn't been called for this lessonId yet.
    if (!startLessonCalled.current) {
      try {
        // Mark as called *before* the API call to prevent race conditions
        startLessonCalled.current = true;
        await startLesson(lessonId);

      } catch (err) {
        // If it fails, allow a retry on the next render cycle.
        startLessonCalled.current = false;
        // We can continue, as getLessonProgress might still work if it was started previously.
      }
    }

    try {
      // Fetch all data concurrently after attempting to start the lesson
      const [lessonData, exercisesData, progressData] = await Promise.all([
        getLessonById(lessonId),
        getExercisesByLessonId(lessonId),
        getLessonProgress(lessonId),
      ]);

      setLesson(lessonData);
      setExercises(exercisesData);
      setLessonProgress(progressData);
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load lesson data.';
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    // When the lessonId changes (e.g., navigating to a new lesson),
    // reset the guard so the new lesson can be started.
    startLessonCalled.current = false;
    fetchLessonData();
  }, [fetchLessonData]); // fetchLessonData has lessonId as a dependency

  const submitExercise = useCallback(async (exerciseId, code, stdin) => {
    setSubmittingExerciseId(exerciseId);
    try {
      const result = await submitExerciseApi(exerciseId, code, stdin);
      toast.success(`Ejercicio "${result.exercise_title}" enviado. Resultado: ${result.is_correct ? 'Correcto' : 'Incorrecto'}`);

      // FIX: Instead of refetching all page data (which causes a loading flicker),
      // we now only refetch the progress information.
      await refetchProgress();

      return result;
    } catch (err) {
      const errorMsg = err.response?.data?.detail || "Error al enviar el ejercicio.";
      toast.error(errorMsg);
      throw err; // Re-throw so the component can handle it if needed
    } finally {
      setSubmittingExerciseId(null);
    }
  }, [refetchProgress]); // Dependency array updated to use the new function.

  const getExerciseProgress = useCallback((exerciseId) => {
    return lessonProgress?.exercises_progress?.find(p => p.exercise_id === exerciseId) || null;
  }, [lessonProgress]);

  const nextLessonInfo = lesson?.next_lesson;

  return {
    lesson,
    exercises,
    isLessonCompleted: lessonProgress?.is_completed || false,
    getExerciseProgress,
    loading,
    error,
    submittingExerciseId,
    submitExercise,
    nextLessonInfo,
  };
}
