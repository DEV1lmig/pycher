import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getLessonById, getExercisesByLessonId, getModuleById, getCourseById } from '@/services/contentService';
import { getLessonProgress, submitExercise as submitExerciseApi, getCurrentCourseExam } from '@/services/progressService';
import { toast } from 'react-hot-toast';
import { contentKeys } from './useContentQueries';

export const lessonKeys = {
  all: ['lessons'],
  detail: (id) => [...lessonKeys.all, 'detail', id],
  exercises: (id) => [...lessonKeys.detail(id), 'exercises'],
  progress: (id) => [...lessonKeys.detail(id), 'progress'],
};

/**
 * Hook to fetch all data related to a single lesson, including its parent module and course for breadcrumbs.
 */
export function useLesson(lessonId, options = {}) {
  const id = parseInt(lessonId, 10);
  const queryClient = useQueryClient();

  const lessonQuery = useQuery({
    queryKey: lessonKeys.detail(id),
    queryFn: () => getLessonById(id),
    enabled: !!id && options.enabled,
  });

  const exercisesQuery = useQuery({
    queryKey: lessonKeys.exercises(id),
    queryFn: () => getExercisesByLessonId(id),
    enabled: !!id && options.enabled,
  });

  const progressQuery = useQuery({
    queryKey: lessonKeys.progress(id),
    queryFn: () => getLessonProgress(id),
    enabled: !!id && options.enabled,
  });

  // Fetch module data only after the lesson data (and thus module_id) is available.
  const moduleQuery = useQuery({
    queryKey: ['module', lessonQuery.data?.module_id],
    queryFn: () => getModuleById(lessonQuery.data.module_id),
    enabled: !!lessonQuery.data?.module_id && options.enabled,
  });

  // Fetch course data only after the module data (and thus course_id) is available.
  const courseQuery = useQuery({
    queryKey: contentKeys.course(moduleQuery.data?.course_id),
    queryFn: () => getCourseById(moduleQuery.data.course_id),
    // This query is enabled only when moduleQuery has successfully fetched data containing a course_id.
    enabled: !!moduleQuery.data?.course_id && options.enabled,
  });

  const submitExerciseMutation = useMutation({
    mutationFn: ({ exerciseId, code, stdin }) => submitExerciseApi(exerciseId, code, stdin),
    onSuccess: (data, variables) => {
      toast.success(`Ejercicio enviado. Resultado: ${data.is_correct ? 'Correcto' : 'Incorrecto'}`);

      // --- FIX: Invalidate BOTH progress and lesson detail ---
      // This ensures we get the latest is_completed status AND the latest next_lesson info.
      queryClient.invalidateQueries({ queryKey: lessonKeys.progress(id) });
      queryClient.invalidateQueries({ queryKey: lessonKeys.detail(id) });

      // If the submission was correct, it might have completed the lesson or module.
      // We must invalidate parent progress queries to reflect these changes across the app.
      if (data.is_correct) {
        const module_id = moduleQuery.data?.id;
        const course_id = courseQuery.data?.id;

        if (module_id) {
          // Invalidate progress for the parent module.
          queryClient.invalidateQueries({ queryKey: contentKeys.moduleProgress([module_id]) });
        }
        if (course_id) {
          // Invalidate progress for the parent course.
          queryClient.invalidateQueries({ queryKey: contentKeys.courseProgress(course_id) });
        }
      }

      // Always invalidate dashboard stats to keep them fresh.
      queryClient.invalidateQueries({ queryKey: contentKeys.dashboardStats() });
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || "Error al enviar el ejercicio.");
    },
  });

  const progress = progressQuery.data;

  // This function now correctly looks for 'exercises_progress' from the backend response.
  const getExerciseProgress = (exerciseId) => {
    if (!progress || !progress.exercises_progress) {
      return null;
    }
    // The backend sends an array, so we find the specific exercise progress by its ID.
    return progress.exercises_progress.find(p => p.exercise_id === exerciseId) || null;
  };

  // Use the 'next_lesson' object directly from the API response.
  const nextLessonInfo = lessonQuery.data?.next_lesson || null;

  return {
    lesson: lessonQuery.data,
    exercises: exercisesQuery.data || [],
    progress: progress,
    module: moduleQuery.data,
    course: courseQuery.data,
    isLessonCompleted: progress?.is_completed || false,
    nextLessonInfo: nextLessonInfo, // Use the direct value from the API
    getExerciseProgress,
    isLoading: lessonQuery.isLoading || exercisesQuery.isLoading || progressQuery.isLoading || moduleQuery.isLoading || courseQuery.isLoading,
    error: lessonQuery.error || exercisesQuery.error || progressQuery.error || moduleQuery.error || courseQuery.error,
    submitExercise: submitExerciseMutation.mutateAsync,
    submittingExerciseId: submitExerciseMutation.isPending ? submitExerciseMutation.variables?.exerciseId : null,
  };
}

/**
 * Hook to fetch data for the final exam of a course.
 */
export function useCourseExam(courseId, options = {}) {
    const id = parseInt(courseId, 10);

    const courseQuery = useQuery({
        queryKey: contentKeys.course(id),
        queryFn: () => getCourseById(id),
        enabled: !!id && options.enabled,
    });

    const examQuery = useQuery({
        queryKey: contentKeys.exam(id),
        queryFn: () => getCurrentCourseExam(id),
        enabled: !!id && options.enabled,
    });

    return {
        course: courseQuery.data,
        examExercise: examQuery.data,
        isLoading: courseQuery.isLoading || examQuery.isLoading,
        error: courseQuery.error || examQuery.error,
    };
}
