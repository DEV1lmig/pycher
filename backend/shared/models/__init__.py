from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
import os

# Create base for all models
Base = declarative_base()

# Import all models to register them with Base
# The order of these imports can sometimes matter if there are complex dependencies
# not resolvable by string-based relationship definitions, but usually SQLAlchemy handles it.
from .content import Course, Module, Lesson, Exercise, CourseExam, UserExamAttempt, CourseRating, UserCourseEnrollment, UserModuleProgress, UserLessonProgress
from .user import User, Progress, UserExerciseSubmission

# Database connection (optional, for standalone scripts that might use these models directly)
# DATABASE_URL = os.getenv("DATABASE_URL")
# if DATABASE_URL:
#     engine = create_engine(DATABASE_URL)
