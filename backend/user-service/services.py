from sqlalchemy.orm import Session, selectinload # Ensure selectinload is imported
from fastapi import HTTPException, status
from datetime import timedelta, datetime
from typing import List, Optional
from sqlalchemy import func, and_, case

# Import all models from your proxy models file
from models import User, UserCourseEnrollment, Course # Ensure Course is imported
from schemas import UserCreate, ProgressCreate, UserEnrollmentWithProgressResponse # Ensure this schema is imported
from utils import get_password_hash, verify_password, create_access_token

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    """Create a new user in the database"""
    try:
        hashed_password = get_password_hash(user.password)

        db_user = User(
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            hashed_password=hashed_password,
            is_active=True
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        return db_user
    except Exception as e:
        db.rollback()
        print(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear usuario"
        )

def authenticate_user(db: Session, username: str, password: str):
    """Authenticate a user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

# --- Progress Tracking Service Functions ---

def enroll_user_in_course(db: Session, user_id: int, course_id: int):
    """Enroll a user in a course"""
    existing_enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()

    if existing_enrollment:
        raise HTTPException(status_code=400, detail="User already enrolled in this course")

    enrollment = UserCourseEnrollment(
        user_id=user_id,
        course_id=course_id
    )

    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment

def start_lesson(db: Session, user_id: int, lesson_id: int):
    """Start a lesson and track progress"""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Create or update lesson progress
    progress = db.query(UserLessonProgress).filter(
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.lesson_id == lesson_id
    ).first()

    if not progress:
        progress = UserLessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            started_at=datetime.utcnow()
        )
        db.add(progress)

    db.commit()
    db.refresh(progress)
    return progress

def complete_exercise(db: Session, user_id: int, exercise_id: int, submitted_code: str, is_correct: bool, output: str = None):
    """Complete an exercise and track submission"""
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    # Create submission record
    submission = UserExerciseSubmission(
        user_id=user_id,
        exercise_id=exercise_id,
        submitted_code=submitted_code,
        is_correct=is_correct,
        output=output,
        score=100 if is_correct else 0
    )

    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission

def get_last_accessed_progress(db: Session, user_id: int):
    """Get user's last accessed course, module, and lesson"""
    last_enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.is_completed == False
    ).order_by(UserCourseEnrollment.last_accessed.desc()).first()

    if not last_enrollment:
        return None

    return {
        "course_id": last_enrollment.course_id,
        "module_id": last_enrollment.last_accessed_module_id,
        "lesson_id": last_enrollment.last_accessed_lesson_id
    }

def get_course_progress_summary(db: Session, user_id: int, course_id: int):
    """Get detailed progress summary for a course"""
    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == user_id,
        UserCourseEnrollment.course_id == course_id
    ).first()

    if not enrollment:
        raise HTTPException(status_code=404, detail="User not enrolled in this course")

    # Get total lessons and completed lessons
    total_lessons = db.query(Lesson).join(Module).filter(Module.course_id == course_id).count()
    completed_lessons = db.query(UserLessonProgress).join(Lesson).join(Module).filter(
        Module.course_id == course_id,
        UserLessonProgress.user_id == user_id,
        UserLessonProgress.is_completed == True
    ).count()

    # Get total exercises and completed exercises
    total_exercises = db.query(Exercise).join(Lesson).join(Module).filter(Module.course_id == course_id).count()
    completed_exercises = db.query(UserExerciseSubmission).join(Exercise).join(Lesson).join(Module).filter(
        Module.course_id == course_id,
        UserExerciseSubmission.user_id == user_id,
        UserExerciseSubmission.is_correct == True
    ).count()

    progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0

    return {
        "course_id": course_id,
        "user_id": user_id,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "completed_exercises": completed_exercises,
        "total_exercises": total_exercises,
        "progress_percentage": progress_percentage,
        "is_course_completed": enrollment.is_completed,
        "last_accessed": enrollment.last_accessed,
        "last_accessed_module_id": enrollment.last_accessed_module_id,
        "last_accessed_lesson_id": enrollment.last_accessed_lesson_id
    }

def update_user(db: Session, user_id: int, user_update: dict):
    """Update user information"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update only provided fields
        for field, value in user_update.items():
            if hasattr(user, field) and value is not None:
                setattr(user, field, value)

        # updated_at will be automatically set by SQLAlchemy due to onupdate=func.now()
        db.commit()
        db.refresh(user)
        return user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating user"
        )

def get_user_enrollments_with_progress(db: Session, user_id: int) -> List[UserCourseEnrollment]:
    """
    Retrieves all course enrollments for a given user, including their progress
    and related course information.
    """
    enrollments = db.query(UserCourseEnrollment).options(
        selectinload(UserCourseEnrollment.course)  # Eagerly load the 'course' relationship
    ).filter(UserCourseEnrollment.user_id == user_id).all()
    return enrollments
