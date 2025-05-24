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
    exams = relationship("CourseExam", back_populates="course", cascade="all, delete-orphan") # New relationship
    enrollments = relationship("UserCourseEnrollment", back_populates="course") # New relationship

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
    user_progress = relationship("UserModuleProgress", back_populates="module") # New relationship

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
    user_progress = relationship("UserLessonProgress", back_populates="lesson") # New relationship

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
    submissions = relationship("UserExerciseSubmission", back_populates="exercise") # New relationship
    # Optionally, add: module = relationship("Module")

class UserCourseEnrollment(Base): # This will serve as UserCourseProgress
    __tablename__ = "user_course_enrollments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    enrollment_date = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True))
    is_completed = Column(Boolean, default=False)
    progress_percentage = Column(Float, default=0.0)
    total_time_spent_minutes = Column(Integer, default=0)
    # New fields for detailed progress
    last_accessed_module_id = Column(Integer, ForeignKey("modules.id"), nullable=True)
    last_accessed_lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)

    course = relationship("Course", back_populates="enrollments")
    # Assuming user_id links to a User table not defined in this file
    # user = relationship("User", back_populates="course_enrollments")
    last_accessed_module = relationship("Module", foreign_keys=[last_accessed_module_id])
    last_accessed_lesson = relationship("Lesson", foreign_keys=[last_accessed_lesson_id])


class UserModuleProgress(Base):
    __tablename__ = "user_module_progress"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False) # Assuming User table exists elsewhere
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed_lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)

    # Relationships
    # user = relationship("User", back_populates="module_progress") # Assuming User model and relationship
    module = relationship("Module", back_populates="user_progress")
    last_accessed_lesson = relationship("Lesson", foreign_keys=[last_accessed_lesson_id])


class UserLessonProgress(Base):
    __tablename__ = "user_lesson_progress"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    is_completed = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    time_spent_minutes = Column(Integer, default=0)
    last_position_seconds = Column(Integer, default=0) # Could be last exercise, or scroll position
    # New field for detailed progress
    last_accessed_exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=True)

    # Relationships
    # user = relationship("User", back_populates="lesson_progress") # Assuming User model and relationship
    lesson = relationship("Lesson", back_populates="user_progress")
    last_accessed_exercise = relationship("Exercise", foreign_keys=[last_accessed_exercise_id])


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
    output = Column(Text, nullable=True) # New field for execution output

    # Relationships
    # user = relationship("User", back_populates="exercise_submissions") # Assuming User model and relationship
    exercise = relationship("Exercise", back_populates="submissions")


class CourseRating(Base):
    __tablename__ = "course_ratings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    rating = Column(Float, nullable=False)
    # comment = Column(Text, nullable=True) # Optional: add comments to ratings
    # created_at = Column(DateTime(timezone=True), server_default=func.now()) # Optional: timestamp

    # Relationships
    # user = relationship("User", back_populates="course_ratings") # Assuming User model
    course = relationship("Course") # Add back_populates if Course has a ratings relationship


# New Models for Exams
class CourseExam(Base):
    __tablename__ = "course_exams"
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    questions = Column(JSONB, nullable=False) # Store questions as JSON
    # Example structure for questions: [{"id": 1, "type": "multiple_choice", "text": "...", "options": ["A", "B"], "answer": "A"}, ...]
    order_index = Column(Integer, nullable=False, default=1)
    pass_threshold_percentage = Column(Float, default=70.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    course = relationship("Course", back_populates="exams")
    attempts = relationship("UserExamAttempt", back_populates="exam", cascade="all, delete-orphan")

class UserExamAttempt(Base):
    __tablename__ = "user_exam_attempts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False) # Assuming User table exists elsewhere
    exam_id = Column(Integer, ForeignKey("course_exams.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    score = Column(Float, nullable=True) # Percentage score
    answers = Column(JSONB, nullable=True) # Store user's answers as JSON
    # Example structure for answers: [{"question_id": 1, "answer": "B"}, ...]
    passed = Column(Boolean, nullable=True) # Calculated based on score and pass_threshold_percentage

    # Relationships
    # user = relationship("User", back_populates="exam_attempts") # Assuming User model
    exam = relationship("CourseExam", back_populates="attempts")
