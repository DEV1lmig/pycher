import { useState, useEffect } from 'react';
import { checkCourseAccess, getUserEnrollments } from '@/services/userService';

export const useCourseAccess = () => {
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEnrollments = async () => {
      try {
        const userEnrollments = await getUserEnrollments();
        setEnrollments(userEnrollments);
      } catch (error) {
        console.error('Error fetching enrollments:', error);
        setEnrollments([]);
      } finally {
        setLoading(false);
      }
    };

    fetchEnrollments();
  }, []);

  const hasAccessToCourse = (courseId) => {
    // Basic course (ID 1) is always accessible
    if (courseId === 1 || courseId === "1") {
      return { hasAccess: true, reason: null };
    }

    // For other courses, check if previous course is completed
    const previousCourseId = courseId - 1;
    const previousCourseProgress = enrollments.find(e => e.course_id === previousCourseId);

    if (!previousCourseProgress || !previousCourseProgress.is_completed) {
      return {
        hasAccess: false,
        reason: `Completa el curso anterior para desbloquear este.`
      };
    }

    return { hasAccess: true, reason: null };
  };

  const getCourseProgress = (courseId) => {
    return enrollments.find(e => e.course_id === courseId);
  };

  return {
    enrollments,
    loading,
    hasAccessToCourse,
    getCourseProgress,
    refreshEnrollments: () => {
      setLoading(true);
      getUserEnrollments().then(setEnrollments).finally(() => setLoading(false));
    }
  };
};
