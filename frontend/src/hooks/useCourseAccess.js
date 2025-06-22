import { useState, useEffect, useCallback } from 'react';
import { getUserEnrollments } from '@/services/userService'; // Assuming this is where it is

export function useCourseAccess() {
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchEnrollments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getUserEnrollments();
      setEnrollments(data || []);
    } catch (err) {
      setError(err);
      setEnrollments([]); // Clear enrollments on error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEnrollments();
  }, [fetchEnrollments]);

  const hasAccessToCourse = useCallback((courseId) => {
    if (loading) return { hasAccess: false, reason: "Cargando..." }; // Or some loading state

    const courseIdNum = parseInt(courseId, 10);

    // Basic course (ID 1) is always accessible
    if (courseIdNum === 1) {
      return { hasAccess: true, reason: null };
    }

    // For other courses, check if previous course is completed
    const previousCourseId = courseIdNum - 1;
    const previousCourseProgress = enrollments.find(e => e.course_id === previousCourseId);

    if (!previousCourseProgress || !previousCourseProgress.is_completed) {
      return {
        hasAccess: false,
        reason: `Debes completar el curso anterior primero.`
      };
    }
    return { hasAccess: true, reason: null };
  }, [enrollments, loading]);

  const getCourseProgress = useCallback((courseId) => {
    if (loading) return null;
    const courseIdNum = parseInt(courseId, 10);
    return enrollments.find(e => e.course_id === courseIdNum) || null;
  }, [enrollments, loading]);

  return {
    enrollments,
    loading,
    error,
    hasAccessToCourse,
    getCourseProgress,
    refreshEnrollments: fetchEnrollments, // Expose the refresh function
  };
}
