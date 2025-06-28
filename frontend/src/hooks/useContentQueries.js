import { useQuery, useMutation, useQueryClient, useQueries } from '@tanstack/react-query';
import { useMemo } from 'react';
import { getAllCourses, getCourseById, getModulesByCourseId, getModuleById, getCourseExamExercises, getLessonsByModuleId } from '@/services/contentService';
import { getCourseProgressSummary, getBatchModuleProgress, getCompletedExercisesCount } from '@/services/progressService';
import { enrollInCourse, unenrollFromCourse } from '@/services/userService';
import { toast } from 'react-hot-toast';

/**
 * A factory for creating consistent query keys.
 * This helps avoid typos and keeps keys organized.
 */
export const contentKeys = {
  all: ['content'],
  courses: () => [...contentKeys.all, 'courses'],
  course: (id) => [...contentKeys.courses(), id],
  courseProgress: (id) => [...contentKeys.course(id), 'progress'],
  coursesProgress: () => [...contentKeys.courses(), 'progress'],
  modules: (courseId) => [...contentKeys.course(courseId), 'modules'],
  moduleProgress: (moduleIds) => [...contentKeys.all, 'modules', 'progress', moduleIds],
  dashboardStats: () => [...contentKeys.all, 'dashboard-stats'],
  exam: (courseId) => [...contentKeys.course(courseId), 'exam'],
  lessons: (moduleId) => [...contentKeys.all, 'modules', moduleId, 'lessons'],
};

/**
 * Custom hook to fetch all courses and their corresponding progress summaries.
 * It handles loading states and returns the combined data.
 */
export function useCourses() {
  // 1. Fetch all courses
  const { data: coursesData = [], isLoading: coursesLoading, error: coursesError } = useQuery({
    queryKey: contentKeys.courses(),
    queryFn: getAllCourses,
  });

  // Memoize the sorted list of courses to ensure a stable order in the UI,
  // preventing cards from re-arranging after enrollment.
  const courses = useMemo(() => {
    return [...coursesData].sort((a, b) => a.id - b.id);
  }, [coursesData]);

  // 2. Fetch progress for all courses, but only after the courses themselves have been loaded.
  const { data: progressMap = {}, isLoading: progressLoading, error: progressError } = useQuery({
    queryKey: contentKeys.coursesProgress(),
    queryFn: async () => {
      const progressEntries = await Promise.all(
        courses.map(async (course) => {
          try {
            const progress = await getCourseProgressSummary(course.id);
            return [course.id, progress];
          } catch {
            return [course.id, null]; // Handle cases where progress might not exist
          }
        })
      );
      return Object.fromEntries(progressEntries);
    },
    // This query will only run if the `courses` query has successfully fetched data.
    enabled: !!courses.length,
  });

  return {
    courses,
    progressMap,
    isLoading: coursesLoading || progressLoading,
    error: coursesError || progressError,
  };
}

/**
 * Custom hook to fetch dashboard statistics like completed exercises count.
 */
export function useDashboardStats() {
  return useQuery({
    queryKey: contentKeys.dashboardStats(),
    queryFn: getCompletedExercisesCount,
    // Provide a default value to prevent errors on the initial render
    initialData: 0,
  });
}

/**
 * Hook to fetch all details for a single course page.
 */
export function useCourseDetail(courseId, isEnrolled) {
  const id = parseInt(courseId, 10);

  const courseQuery = useQuery({
    queryKey: contentKeys.course(id),
    queryFn: () => getCourseById(id),
    enabled: !!id,
  });

  const modulesQuery = useQuery({
    queryKey: contentKeys.modules(id),
    queryFn: () => getModulesByCourseId(id),
    enabled: !!id,
  });

  // Fetch lesson counts for each module in parallel once the modules are loaded.
  const moduleLessonCounts = useQueries({
    queries: (modulesQuery.data || []).map(module => ({
      queryKey: contentKeys.lessons(module.id),
      queryFn: () => getLessonsByModuleId(module.id),
      select: (lessons) => lessons.length, // We only need the count from the response.
      enabled: !!modulesQuery.data,
      staleTime: 10 * 60 * 1000, // Cache lesson counts for 10 minutes.
    })),
  });

  // Combine the module data with the fetched lesson counts.
  const modulesWithLessonCounts = useMemo(() => {
    return (modulesQuery.data || []).map((module, index) => {
      const countResult = moduleLessonCounts[index];
      return {
        ...module,
        // The ModuleCard will show the count, or 0 as a fallback.
        lessonCount: countResult.isSuccess ? countResult.data : undefined,
      };
    });
  }, [modulesQuery.data, moduleLessonCounts]);

  // Centralize the final module lock state logic here.
  const finalModules = useMemo(() => {
    // Use the enrollment status passed from the component, which is the single source of truth.
    return (modulesWithLessonCounts || []).map(module => ({
      ...module,
      // A module is locked if the user is not enrolled OR if the module itself is marked as locked by the backend.
      is_locked: !isEnrolled || module.is_locked,
    }));
  }, [modulesWithLessonCounts, isEnrolled]);

  const courseProgressQuery = useQuery({
    queryKey: contentKeys.courseProgress(id),
    queryFn: async () => {
      try {
        // Attempt to fetch the user's progress for this course.
        return await getCourseProgressSummary(id);
      } catch (error) {
        // A 404 status means the user is not enrolled, which is a valid state
        // for viewing a course page. We return null instead of throwing an error.
        if (error.response && error.response.status === 404) {
          return null;
        }
        // For any other type of error, we let TanStack Query handle it.
        throw error;
      }
    },
    enabled: !!id,
  });

  const moduleIds = modulesQuery.data?.map(mod => mod.id) || [];
  const moduleProgressQuery = useQuery({
    queryKey: contentKeys.moduleProgress(moduleIds),
    queryFn: () => getBatchModuleProgress(moduleIds),
    enabled: !!moduleIds.length,
  });

  const examQuery = useQuery({
    queryKey: contentKeys.exam(id),
    queryFn: async () => {
      try {
        // Attempt to fetch the exam exercises
        return await getCourseExamExercises(id);
      } catch (error) {
        // If the server responds with 404, it likely means no exam exists for this course.
        // We can treat this as a non-error state by returning null.
        if (error.response && error.response.status === 404) {
          return null;
        }
        // For all other errors, we re-throw them to let react-query handle them.
        throw error;
      }
    },
    enabled: !!id,
  });

  // Determine the overall loading state, including the new lesson count queries.
  const areLessonCountsLoading = moduleLessonCounts.some(q => q.isLoading);

  return {
    course: courseQuery.data,
    modules: finalModules, // Return the modules with the final, calculated lock state.
    courseProgress: courseProgressQuery.data,
    moduleProgresses: moduleProgressQuery.data || {},
    examExercise: examQuery.data,
    isLoading: courseQuery.isLoading || modulesQuery.isLoading || courseProgressQuery.isLoading || areLessonCountsLoading,
    error: courseQuery.error || modulesQuery.error || courseProgressQuery.error || examQuery.error,
  };
}

/**
 * Hook to fetch details for a module page (module, its lessons, and parent course).
 */
export function useModuleDetail(moduleId) {
    const id = parseInt(moduleId, 10);

    const moduleQuery = useQuery({
        queryKey: ['module', id],
        queryFn: () => getModuleById(id),
        enabled: !!id,
    });

    const courseId = moduleQuery.data?.course_id;
    const courseQuery = useQuery({
        queryKey: contentKeys.course(courseId),
        queryFn: () => getCourseById(courseId),
        enabled: !!courseId,
    });

    const lessonsQuery = useQuery({
        queryKey: contentKeys.lessons(id),
        queryFn: () => getLessonsByModuleId(id),
        enabled: !!id,
    });

    return {
        module: moduleQuery.data,
        course: courseQuery.data,
        lessons: lessonsQuery.data || [],
        isLoading: moduleQuery.isLoading || courseQuery.isLoading || lessonsQuery.isLoading,
        error: moduleQuery.error || courseQuery.error || lessonsQuery.error,
    };
}

/**
 * Hook for managing course enrollment actions.
 */
export function useEnrollmentActions() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({ courseId, action }) => {
      if (action === 'enroll') return enrollInCourse(courseId);
      if (action === 'unenroll') return unenrollFromCourse(courseId);
      throw new Error('Invalid action');
    },
    // When a mutation is called, we can optimistically update the UI
    onMutate: async ({ courseId, action }) => {
      const courseQueryKey = contentKeys.course(courseId);
      const progressQueryKey = contentKeys.courseProgress(courseId);
      const modulesQueryKey = contentKeys.modules(courseId);
      const enrollmentsQueryKey = ['user', 'enrollments'];

      // Cancel any outgoing refetches so they don't overwrite our optimistic update
      await queryClient.cancelQueries({ queryKey: courseQueryKey });
      await queryClient.cancelQueries({ queryKey: progressQueryKey });
      await queryClient.cancelQueries({ queryKey: modulesQueryKey });
      await queryClient.cancelQueries({ queryKey: enrollmentsQueryKey });

      // Snapshot the previous values from the cache
      const previousCourseData = queryClient.getQueryData(courseQueryKey);
      const previousProgressData = queryClient.getQueryData(progressQueryKey);
      const previousModulesData = queryClient.getQueryData(modulesQueryKey);
      const previousEnrollments = queryClient.getQueryData(enrollmentsQueryKey);

      const moduleIds = previousModulesData?.map(m => m.id) || [];
      const moduleProgressQueryKey = contentKeys.moduleProgress(moduleIds);
      await queryClient.cancelQueries({ queryKey: moduleProgressQueryKey });
      const previousModuleProgresses = queryClient.getQueryData(moduleProgressQueryKey);

      // Optimistically update the student count
      if (previousCourseData) {
        queryClient.setQueryData(courseQueryKey, {
          ...previousCourseData,
          students_count: action === 'enroll'
            ? previousCourseData.students_count + 1
            : Math.max(0, previousCourseData.students_count - 1),
        });
      }

      if (action === 'enroll') {
        // Optimistically update the global enrollments list with a complete mock object.
        if (previousEnrollments) {
          const optimisticEnrollment = {
            id: -1, // Temporary ID
            user_id: -1, // Placeholder
            course_id: courseId,
            is_active_enrollment: true, // This is the key change
            is_completed: false,
            progress_percentage: 0,
            enrollment_date: new Date().toISOString(),
            last_accessed: new Date().toISOString(),
            total_time_spent_minutes: 0,
            last_accessed_module_id: null,
            last_accessed_lesson_id: null,
            exam_unlocked: false,
          };
          queryClient.setQueryData(enrollmentsQueryKey, [...previousEnrollments, optimisticEnrollment]);
        }

        // Optimistically set course progress to a "just started" state
        queryClient.setQueryData(progressQueryKey, { progress_percentage: 0, is_course_completed: false, exam_unlocked: false });

      } else { // 'unenroll'
        // Optimistically update the specific enrollment to be inactive.
        if (previousEnrollments) {
            const newEnrollments = previousEnrollments.map(e =>
                e.course_id === courseId ? { ...e, is_active_enrollment: false } : e
            );
            queryClient.setQueryData(enrollmentsQueryKey, newEnrollments);
        }
        // Set progress back to an unenrolled state.
        queryClient.setQueryData(progressQueryKey, null);
      }

      // Return a context object with all snapshotted values for potential rollback
      return { previousCourseData, previousProgressData, previousModulesData, previousModuleProgresses, previousEnrollments, moduleProgressQueryKey };
    },
    // If the mutation fails, use the context returned from onMutate to roll back
    onError: (err, variables, context) => {
      // Rollback all optimistic updates to their previous state
      if (context?.previousCourseData) {
        queryClient.setQueryData(contentKeys.course(variables.courseId), context.previousCourseData);
      }
      if (context?.previousProgressData !== undefined) {
        queryClient.setQueryData(contentKeys.courseProgress(variables.courseId), context.previousProgressData);
      }
      if (context?.previousModulesData) {
        queryClient.setQueryData(contentKeys.modules(variables.courseId), context.previousModulesData);
      }
      if (context?.previousModuleProgresses) {
        queryClient.setQueryData(context.moduleProgressQueryKey, context.previousModuleProgresses);
      }
      if (context?.previousEnrollments) {
        queryClient.setQueryData(['user', 'enrollments'], context.previousEnrollments);
      }
      toast.error(err.response?.data?.detail || "Ocurrió un error.");
    },
    onSuccess: (data, variables) => {
      toast.success(`Acción completada con éxito.`);
      // By invalidating here, AFTER the mutation is confirmed successful,
      // we ensure the server has processed the change before we refetch.
      const courseId = variables.courseId;
      queryClient.invalidateQueries({ queryKey: contentKeys.course(courseId) });
      queryClient.invalidateQueries({ queryKey: contentKeys.courses() });
      queryClient.invalidateQueries({ queryKey: ['user', 'enrollments'] });
    },
    // onSettled runs for both success and error, but we now handle invalidation
    // specifically on success to avoid the race condition.
    onSettled: () => {
      // We can leave this empty or use it for logic that must run regardless of outcome,
      // but the key invalidations are now in onSuccess.
    },
  });

  return mutation;
}
