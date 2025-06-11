from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from . import Base  # IMPORT THE SHARED BASE

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    exercise_submissions = relationship("UserExerciseSubmission", back_populates="user", cascade="all, delete-orphan")
    # progress_records = relationship("Progress", back_populates="user") # If you want a direct link from User to Progress

class Progress(Base):
    __tablename__ = "user_progress" # This table name seems more generic than UserModuleProgress or UserLessonProgress
                                     # Consider if this is distinct from UserModuleProgress and UserLessonProgress in content.py
                                     # If it's the same as UserLessonProgress, it might be redundant or need consolidation.
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True) # Nullable if not completed

    user = relationship("User") # Add back_populates="progress_records" if User has this relationship
    lesson = relationship("Lesson") # Add back_populates if Lesson has a relationship to Progress
    # The relationship below seems to imply a Progress record can have multiple submissions, which might be unusual.
    # Typically, a UserExerciseSubmission links directly to a User and an Exercise.
    # If Progress is per-lesson, and submissions are per-exercise, this link might need rethinking
    # or UserExerciseSubmission should have a ForeignKey to Progress.id if that's the intent.
    # For now, commenting out as it might conflict with User.exercise_submissions.
    # exercise_submissions = relationship("UserExerciseSubmission", back_populates="progress")


class UserExerciseSubmission(Base):
    __tablename__ = "user_exercise_submissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # ADDED ForeignKey
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    code_submitted = Column(Text, nullable=False)
    passed = Column(Boolean, default=False)
    output = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True) # Optional feedback from the instructor or system
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    execution_time = Column(Float, nullable=True)
    # progress_id = Column(Integer, ForeignKey("user_progress.id"), nullable=True) # If a submission belongs to a specific progress entry
    is_correct = Column(Boolean, default=False) # This might be redundant with 'passed', but kept for clarity
    exercise = relationship("Exercise", back_populates="submissions")
    attempt_number = Column(Integer, nullable=True) # Track the number of attempts for this submission
    lesson = relationship("Lesson", back_populates="exercise_submissions")
    user = relationship("User", back_populates="exercise_submissions") # UNCOMMENTED and corrected
    # progress = relationship("Progress", back_populates="exercise_submissions") # If linking to Progress table
