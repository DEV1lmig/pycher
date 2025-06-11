# Import models from shared location
from shared.models import Base, User, UserModuleProgress, UserLessonProgress, Course, Module, Lesson, Exercise, UserCourseEnrollment, CourseRating

# Re-export for backward compatibility
__all__ = ['Base', 'User', 'UserModuleProgress', 'UserLessonProgress', 'Course', 'Module', 'Lesson', 'Exercise', 'UserCourseEnrollment', 'CourseRating']
