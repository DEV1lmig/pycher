import { useState, useEffect, useCallback } from 'react';
import {
  getLessonById,
  getExercisesByLessonId,
  getNextLessonInfo
} from '@/services/contentService';
import {
  startLesson,
  getLessonDetailedProgress
} from '@/services/userService';
import { submitExercise as submitExerciseApi } from '@/services/progressService';
import { toast } from 'react-hot-toast';

export function useLessonDetail(lessonId) {
  const [lesson, setLesson] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [lessonProgress, setLessonProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submittingExerciseId, setSubmittingExerciseId] = useState(null);
  const [nextLessonInfo, setNextLessonInfo] = useState(null);
  const [isLessonCompleted, setIsLessonCompleted] = useState(false);

  const fetchData = useCallback(async () => {
    if (!lessonId) {
      setLoading(false);
      setError("No Lesson ID provided."); // Set an error if lessonId is missing
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // Attempt to mark the lesson as started.
      // Backend should handle cases where it's already started or user isn't enrolled.
      try {
        await startLesson(lessonId);
      } catch (startError) {
        // This error might not be critical if it's due to the lesson already being started.
        // More critical errors (like 404 for the lesson) will likely be caught by subsequent API calls.
        console.warn(`Attempt to start lesson ${lessonId} encountered an issue (this might be expected):`, startError.message);
      }

      const [lessonData, exercisesData] = await Promise.all([
        getLessonById(lessonId),
        getExercisesByLessonId(lessonId),
      ]);

      setLesson(lessonData);
      // Ensure exercisesData is an array; default to empty array if not.
      setExercises(Array.isArray(exercisesData) ? exercisesData : []);

      // Log progress fetching
      console.log(`useLessonDetail: Fetching progress for lesson ${lessonId}`);
      const progressData = await getLessonDetailedProgress(lessonId); // From userService
      console.log('useLessonDetail: Received progressData:', progressData); // <--- LOG THIS

      if (progressData) {
        setLessonProgress(progressData);
        const completed = progressData.is_completed || false; // Check the structure of progressData
        console.log(`useLessonDetail: Setting isLessonCompleted from fetchData to: ${completed}`); // <--- LOG THIS
        setIsLessonCompleted(completed);

        if (completed) {
          console.log(`useLessonDetail: Lesson ${lessonId} is completed, fetching next lesson info.`);
          const nextInfo = await getNextLessonInfo(lessonId); // From contentService
          console.log('useLessonDetail: Received nextLessonInfo from fetchData:', nextInfo); // <--- LOG THIS
          setNextLessonInfo(nextInfo);
        } else {
          setNextLessonInfo(null); // Clear if lesson is not completed
        }
      } else {
        console.warn(`useLessonDetail: No progressData received for lesson ${lessonId}`);
        setIsLessonCompleted(false);
        setNextLessonInfo(null);
      }
    } catch (err) {
      console.error(`Error fetching data for lesson ${lessonId}:`, err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load lesson data.';
      setError(errorMessage);
      toast.error(errorMessage);
      // Reset state on error
      setLesson(null);
      setExercises([]);
      setLessonProgress(null);
    } finally {
      setLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]); // `fetchData` is memoized with `useCallback`

  const handleExerciseSubmit = async (exerciseId, submittedCode, userInputData) => {
    if (!lessonId) {
      toast.error("Cannot submit exercise: Lesson ID is missing.");
      return null; // Or throw an error
    }
    setSubmittingExerciseId(exerciseId);
    try {
      const result = await submitExerciseApi(exerciseId, submittedCode, userInputData);
      toast.success(`Ejercicio "${result.exercise_title || exerciseId}" ${result.is_correct ? 'completado correctamente!' : 'enviado.'}`);

      // Re-fetch detailed progress for the entire lesson
      console.log(`useLessonDetail: Re-fetching progress for lesson ${lessonId} after exercise submission.`);
      const updatedProgressData = await getLessonDetailedProgress(lessonId);
      console.log('useLessonDetail: Received updatedProgressData after submission:', updatedProgressData); // <--- LOG THIS

      if (updatedProgressData) {
        setLessonProgress(updatedProgressData);
        const completed = updatedProgressData.is_completed || false;
        console.log(`useLessonDetail: Setting isLessonCompleted from handleExerciseSubmit to: ${completed}`); // <--- LOG THIS
        setIsLessonCompleted(completed);

        if (completed) {
          console.log(`useLessonDetail: Lesson ${lessonId} is completed after submission, fetching next lesson info.`);
          const nextInfo = await getNextLessonInfo(lessonId);
          console.log('useLessonDetail: Received nextLessonInfo from handleExerciseSubmit:', nextInfo); // <--- LOG THIS
          setNextLessonInfo(nextInfo);
        } else {
          setNextLessonInfo(null); // Clear if lesson is not completed
        }
      } else {
         console.warn(`useLessonDetail: No updatedProgressData received for lesson ${lessonId} after submission.`);
        setIsLessonCompleted(false);
        setNextLessonInfo(null);
      }
      return result;
    } catch (err) {
      console.error(`Error submitting exercise ${exerciseId} for lesson ${lessonId}:`, err);
      const errorMessage = err.response?.data?.detail || err.message || 'Error al enviar el ejercicio.';
      toast.error(errorMessage);
      throw err; // Re-throw so the component can potentially handle it
    } finally {
      setSubmittingExerciseId(null);
    }
  };

  // Derived state: checks if the lesson is marked as completed.
  // const isLessonCompleted = lessonProgress?.is_completed || false;

  // Helper function to find progress for a specific exercise.
  const getExerciseProgress = (exerciseId) => {
    return lessonProgress?.exercises_progress?.find(ep => ep.exercise_id === exerciseId) || null;
  };

  return {
    lesson,
    exercises,
    lessonProgress,
    isLessonCompleted,
    getExerciseProgress,
    nextLessonInfo, // This will contain { id, title, module_id, module_title } or similar
    loading,
    error,
    submittingExerciseId,
    refreshData: fetchData, // Expose a way to manually refresh data
    submitExercise: handleExerciseSubmit,
  };
}
