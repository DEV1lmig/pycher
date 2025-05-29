from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
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

class Progress(Base):
    __tablename__ = "user_progress"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False) # Relies on Lesson from content.py
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True))

    # user = relationship("User") # Define back_populates if User has a relationship to Progress
    # lesson = relationship("Lesson") # Define back_populates if Lesson has a relationship to Progress
    exercise_submissions = relationship("UserExerciseSubmission", back_populates="progress")


class UserExerciseSubmission(Base): # This is now the canonical definition
    __tablename__ = "user_exercise_submissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False) # ADD THIS LINE

    # Aligning with previous discussions and potential needs:
    submitted_code = Column(Text, nullable=True) # Was missing, often needed
    output = Column(Text, nullable=True) # Was missing
    is_correct = Column(Boolean, nullable=False, default=False) # Was missing
    attempt_number = Column(Integer, nullable=False, default=1) # Was missing
    execution_time_ms = Column(Integer, nullable=True) # Was missing

    # submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) # Existing
    submitted_at = Column(DateTime, default=datetime.utcnow) # Changed to match previous good version
    score = Column(Integer, nullable=True) # Existing, but consider default=0
    # max_score = Column(Integer, nullable=True) # Consider if this is needed or derived
    user_progress_id = Column(Integer, ForeignKey("user_progress.id"), nullable=True)

    user = relationship("User", back_populates="exercise_submissions")
    exercise = relationship("Exercise", back_populates="submissions")
    lesson = relationship("Lesson", back_populates="exercise_submissions") # ADD THIS RELATIONSHIP
    progress = relationship("Progress", back_populates="exercise_submissions")
