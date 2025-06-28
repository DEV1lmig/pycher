import { useQuery } from '@tanstack/react-query';
import { useCallback } from 'react';
import { getUserEnrollments } from '@/services/userService';

// Define a consistent query key for user enrollments.
const userKeys = {
  all: ['user'],
  enrollments: () => [...userKeys.all, 'enrollments'],
};

/**
 * A modern, TanStack Query-powered hook to manage user course access rights.
 * This hook is the single source of truth for determining if a user is enrolled
 * in a course and if they have met the prerequisites to access it.
 */
export function useCourseAccess() {
  const { data: enrollments = [], isLoading, error } = useQuery({
    queryKey: userKeys.enrollments(),
    queryFn: getUserEnrollments,
    // Provide an empty array as initial data to prevent errors on first render.
    initialData: [],
    // Cache enrollment data for 5 minutes to reduce unnecessary network requests.
    staleTime: 5 * 60 * 1000,
  });

  /**
   * Checks if a user has access to a specific course and their enrollment status.
   * @param {number | string} courseId - The ID of the course to check.
   * @returns {{hasAccess: boolean, isEnrolled: boolean, reason: string | null}}
   */
  const hasAccessToCourse = useCallback((courseId) => {
    if (isLoading) {
      return { hasAccess: false, isEnrolled: false, reason: "Cargando..." };
    }

    const courseIdNum = parseInt(courseId, 10);
    const enrollment = enrollments.find(e => e.course_id === courseIdNum);
    const isEnrolled = !!(enrollment && enrollment.is_active_enrollment);

    // The first course is always accessible as a starting point.
    if (courseIdNum === 1) {
      return { hasAccess: true, isEnrolled, reason: null };
    }

    // For subsequent courses, check if the prerequisite (previous course) is completed.
    const previousCourseId = courseIdNum - 1;
    const previousCourseEnrollment = enrollments.find(e => e.course_id === previousCourseId);

    if (!previousCourseEnrollment || !previousCourseEnrollment.is_completed) {
      return {
        hasAccess: false,
        isEnrolled,
        reason: `Debes completar el curso anterior primero.`
      };
    }

    return { hasAccess: true, isEnrolled, reason: null };
  }, [enrollments, isLoading]);

  return {
    enrollments,
    isLoading,
    error,
    hasAccessToCourse,
  };
}
