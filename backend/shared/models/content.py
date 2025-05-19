from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from . import Base


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    level = Column(String, nullable=False)
    duration_minutes = Column(Integer)
    students_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    image_url = Column(String)
    color_theme = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")

    @property
    def total_modules(self):
        return len(self.modules)  # Automatically computed from the relationship

class Module(Base):  # <-- Change from Modules to Module
    __tablename__ = "modules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    duration_minutes = Column(Integer)
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")
    course = relationship("Course", back_populates="modules")

class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(Integer, primary_key=True, autoincrement=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False)
    duration_minutes = Column(Integer)
    module = relationship("Module", back_populates="lessons")
    exercises = relationship("Exercise", back_populates="lesson")

class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=True)
    order_index = Column(Integer, nullable=False, default=1)  # <-- Add this line
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    instructions = Column(Text)
    starter_code = Column(Text)
    solution_code = Column(Text)
    test_cases = Column(Text)
    hints = Column(Text)
    lesson = relationship("Lesson", back_populates="exercises")
    # Optionally, add: module = relationship("Module")

class UserCourseEnrollment(Base):
    __tablename__ = "user_course_enrollments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrollment_date = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True))
    is_completed = Column(Boolean, default=False)
    progress_percentage = Column(Float, default=0.0)
    total_time_spent_minutes = Column(Integer, default=0)

class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    time_spent_minutes = Column(Integer, default=0)
    last_position_seconds = Column(Integer, default=0)

class UserExerciseSubmission(Base):
    __tablename__ = "user_exercise_submissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    submitted_code = Column(Text)
    is_correct = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    execution_time_ms = Column(Integer)
    score = Column(Integer, default=0)

class CourseRating(Base):
    __tablename__ = "course_ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    rating = Column(Float, nullable=False)
