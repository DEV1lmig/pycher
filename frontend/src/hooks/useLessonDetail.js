import { useState, useEffect, useCallback } from 'react';
import { getLessonById, getExercisesByLessonId } from '@/services/contentService';
// --- FIX: Import all progress functions from the consolidated progressService ---
import progressService from '@/services/progressService';
import { toast } from 'react-hot-toast';

export function useLessonDetail(lessonId) {
  const [lesson, setLesson] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [lessonProgress, setLessonProgress] = useState(null);
  const [exercisesProgress, setExercisesProgress] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submittingExerciseId, setSubmittingExerciseId] = useState(null);
  const [nextLessonInfo, setNextLessonInfo] = useState(null);

  // --- START: NEW FUNCTION FOR SOFT UPDATE ---
  const updateExerciseProgress = useCallback((exerciseId, isCorrect) => {
    setExercisesProgress(prevProgress => ({
      ...prevProgress,
      [exerciseId]: {
        ...(prevProgress[exerciseId] || {}),
        is_correct: isCorrect,
        attempts: (prevProgress[exerciseId]?.attempts || 0) + 1,
      }
    }));
  }, []);
  // --- END: NEW FUNCTION FOR SOFT UPDATE ---

  const fetchLessonData = useCallback(async () => {
    if (!lessonId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [lessonData, exercisesData, progressData] = await Promise.all([
        getLessonById(lessonId),
        getExercisesByLessonId(lessonId),
        progressService.getLessonProgress(lessonId),
      ]);
      console.log("Fetched lesson progressData:", progressData); // <--- LOG HERE
      setLesson(lessonData);
      setExercises(Array.isArray(exercisesData) ? exercisesData : []);
      setLessonProgress(progressData);

      // --- CONSOLE LOG FOR NEXT LESSON ---
      console.log("Next lesson info from API:", progressData?.next_lesson_info);
      // --- END CONSOLE LOG ---

      setNextLessonInfo(progressData?.next_lesson_info || null);

      const exerciseProgressMap = {};
      if (progressData?.exercises_progress) {
        progressData.exercises_progress.forEach(p => {
          exerciseProgressMap[p.exercise_id] = p;
        });
      }
      setExercisesProgress(exerciseProgressMap);
    } catch (err) {
      setError(err.response?.data?.detail || `Error al cargar la lección ${lessonId}.`);
    } finally {
      setLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    fetchLessonData();
  }, [fetchLessonData]);

  const submitExercise = useCallback(async (exerciseId, code, inputData, options = {}) => {
    setSubmittingExerciseId(exerciseId);
    try {
      const result = await progressService.submitExercise(exerciseId, code, inputData);

      updateExerciseProgress(exerciseId, result.is_correct);

      if (result.is_correct) {
        progressService.getLessonProgress(lessonId).then(setLessonProgress);
      }

      // --- FIX: Only show default toasts if not disabled by options ---
      if (!options.disableToast) {
        if (result.is_correct) {
          toast.success('¡Ejercicio correcto!');
        } else {
          toast.error(result.validation_result?.error || 'Respuesta incorrecta.');
        }
      }
      return result;
    } catch (error) {
      if (!options.disableToast) {
        toast.error(error.response?.data?.detail || 'Error al enviar el ejercicio.');
      }
      throw error; // Re-throw error so the calling component can handle it
    } finally {
      setSubmittingExerciseId(null);
    }
  }, [lessonId, updateExerciseProgress]); // <-- Updated dependencies

  const getExerciseProgress = useCallback((exerciseId) => {
    return exercisesProgress[exerciseId] || null;
  }, [exercisesProgress]);

  const isLessonCompleted = lessonProgress?.is_completed || false;

  return {
    lesson,
    exercises,
    isLessonCompleted,
    getExerciseProgress,
    loading,
    error,
    submittingExerciseId,
    submitExercise,
    nextLessonInfo,
  };
}
