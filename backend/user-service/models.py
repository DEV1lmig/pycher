# Import models from shared location
import os
from sqlalchemy import create_engine
from shared.models import Base, User, Progress, UserCourseEnrollment, UserModuleProgress, UserLessonProgress,UserExerciseSubmission, Course, Module, Lesson, Exercise, CourseExam, UserExamAttempt

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)

# Re-export for backward compatibility
__all__ = ['Base', 'User', 'Progress', 'UserCourseEnrollment', 'UserModuleProgress', 'UserLessonProgress', 'UserExerciseSubmission', 'Course', 'Module', 'Lesson', 'Exercise', 'CourseExam', 'UserExamAttempt']
