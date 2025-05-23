import logging
import re
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm  # Add this import
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import timedelta, datetime
from database import get_db
from jose import jwt, JWTError

# Import models from your proxy
from models import User, UserCourseEnrollment, UserModuleProgress, UserLessonProgress, UserExerciseSubmission, CourseExam, UserExamAttempt

from schemas import (
    UserCreate, UserResponse, Token, UserLogin,
    UserCourseProgressResponse,
    UserModuleProgressResponse,
    UserLessonProgressResponse,
    ExerciseCompletionRequest,
    UserExerciseSubmissionResponse,
    UserExamAttemptResponse,
    ExamAnswersRequest,
    LastAccessedProgressResponse,
    CourseProgressSummaryResponse,
    UserEnrollmentWithProgressResponse,
    CourseExamSchema
)

from services import (
    get_user, get_user_by_username, get_user_by_email, create_user, authenticate_user,
    enroll_user_in_course, start_lesson, complete_exercise, get_last_accessed_progress,
    get_course_progress_summary, get_user_enrollments_with_progress
)

from utils import create_access_token, redis_client, SECRET_KEY, ALGORITHM
from auth import get_current_user

router = APIRouter()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("user-service-progress")

# --- Auth Routes (register, token, logout, refresh, me) ---

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Log the registration attempt (omit password)
    logger.info(f"Registration attempt - Username: {user.username}, Email: {user.email}")

    db_user = get_user_by_username(db, user.username)
    if db_user:
        logger.warning(f"Registration failed - Username already exists: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre de usuario ya registrado"
        )
    db_email = get_user_by_email(db, user.email)
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email ya registrado"
        )

    logger.info(f"User registered successfully - Username: {user.username}")
    new_user = create_user(db, user)
    return new_user

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Manual validation to match UserLogin schema
    username = form_data.username
    password = form_data.password

    # Username: 3-64 chars, allowed chars
    if not re.fullmatch(r"^[a-zA-Z0-9_.@-]{3,64}$", username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Formato de usuario inválido"
        )
    # Password: 8-64 chars
    if not (8 <= len(password) <= 64):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La contraseña debe tener entre 8 y 64 caracteres"
        )

    # Log the login attempt (omit password)
    logger.info(f"Login attempt - Username: {form_data.username}")

    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Login failed: Invalid credentials - Username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log successful login
    logger.info(f"Login successful - Username: {form_data.username}, User ID: {user.id}")

    access_token_expires = timedelta(minutes=30)
    refresh_token_expires = timedelta(days=7)

    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}, expires_delta=access_token_expires
    )
    refresh_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "type": "refresh"}, expires_delta=refresh_token_expires
    )

    # Log token storage
    logger.info(f"Generated tokens for user: {form_data.username}")

    # Store tokens in Redis
    try:
        redis_client.setex(
            f"token:{user.username}",
            int(access_token_expires.total_seconds()),
            access_token
        )
        redis_client.setex(
            f"refresh_token:{user.username}",
            int(refresh_token_expires.total_seconds()),
            refresh_token
        )
        logger.info(f"Stored tokens in Redis for user: {form_data.username}")
    except Exception as e:
        logger.warning(f"Failed to store tokens in Redis: {e}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout_user(current_user: User = Depends(get_current_user)):
    # Remove token from Redis
    redis_client.delete(f"token:{current_user.username}")
    redis_client.delete(f"refresh_token:{current_user.username}")
    logger.info(f"Logout for user: {current_user.username}")
    return {"detail": "Desconectado correctamente"}

@router.post("/refresh", response_model=Token)
def refresh_access_token(refresh_token_body: Dict[str, str] = Body(...), db: Session = Depends(get_db)):
    refresh_token = refresh_token_body.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh token not provided")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudo validar el token de actualización",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        token_type: str = payload.get("type")
        if username is None or user_id is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Verify refresh token is in Redis
    stored_refresh_token = redis_client.get(f"refresh_token:{username}")
    if stored_refresh_token is None or stored_refresh_token.decode() != refresh_token:
        raise credentials_exception

    # Create new access token
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception

    access_token_expires = timedelta(minutes=30)
    new_access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id}, expires_delta=access_token_expires
    )

    # Update access token in Redis
    redis_client.setex(
        f"token:{username}",
        int(access_token_expires.total_seconds()),
        new_access_token
    )

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# --- Progress Tracking Routes ---

@router.post("/courses/{course_id}/enroll", response_model=UserCourseProgressResponse)
def enroll_in_course_route(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    enrollment = enroll_user_in_course(db, current_user.id, course_id)
    return enrollment

@router.get("/users/me/enrollments", response_model=List[UserEnrollmentWithProgressResponse])
def get_my_enrollments_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_enrollments_with_progress(db, current_user.id)


@router.post("/progress/last-accessed", response_model=UserCourseProgressResponse) # Or a more specific response
def update_last_accessed_route(
    course_id: int,
    module_id: Optional[int] = Body(None, embed=True),
    lesson_id: Optional[int] = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return update_last_accessed(db, current_user.id, course_id, module_id, lesson_id)

@router.get("/progress/last-accessed", response_model=Optional[LastAccessedProgressResponse])
def get_last_accessed_route(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content = get_last_accessed_content(db, current_user.id)
    if not content:
        return None
    return content

@router.post("/modules/{module_id}/start", response_model=UserModuleProgressResponse)
def start_module_route(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return start_module(db, current_user.id, module_id)

@router.post("/modules/{module_id}/complete", response_model=UserModuleProgressResponse)
def complete_module_route(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return complete_module(db, current_user.id, module_id)

@router.get("/modules/{module_id}/progress", response_model=Optional[UserModuleProgressResponse])
def get_module_progress_route(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_module_progress(db, current_user.id, module_id)

@router.post("/lessons/{lesson_id}/start", response_model=UserLessonProgressResponse)
def start_lesson_route(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return start_lesson(db, current_user.id, lesson_id)

@router.post("/lessons/{lesson_id}/complete", response_model=UserLessonProgressResponse)
def complete_lesson_route(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return complete_lesson(db, current_user.id, lesson_id)

@router.get("/lessons/{lesson_id}/progress", response_model=Optional[UserLessonProgressResponse])
def get_lesson_progress_route(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_lesson_progress(db, current_user.id, lesson_id)

@router.post("/exercises/{exercise_id}/submit", response_model=UserExerciseSubmissionResponse)
def submit_exercise_route(
    exercise_id: int,
    submission_data: ExerciseCompletionRequest, # Changed from ExerciseSubmissionRequest
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return submit_exercise(
        db, current_user.id, exercise_id,
        submission_data.submitted_code, submission_data.is_correct,
        None # submission_data.output - ExerciseCompletionRequest does not have output yet
             # If you want to pass output, add it to ExerciseCompletionRequest schema
    )

@router.get("/courses/{course_id}/progress-summary", response_model=CourseProgressSummaryResponse)
def get_course_progress_summary_route(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_course_progress_summary(db, current_user.id, course_id)

# --- Exam Routes ---

@router.get("/courses/{course_id}/exam", response_model=Optional[CourseExamSchema]) # Changed to use defined CourseExamSchema
def get_course_exam_route(
    course_id: int,
    # exam_id: Optional[int] = None, # If you want to specify one, or just get the default/first
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Ensure user is enrolled or has access
):
    # Basic check: user enrolled in course?
    enrollment = db.query(UserCourseEnrollment).filter(
        UserCourseEnrollment.user_id == current_user.id,
        UserCourseEnrollment.course_id == course_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not enrolled in this course")

    exam = get_course_exam(db, course_id)
    if not exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exam not found for this course")
    return exam # Pydantic will serialize CourseExam model

@router.post("/exams/{exam_id}/start-attempt", response_model=UserExamAttemptResponse)
def start_exam_attempt_route(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return start_exam_attempt(db, current_user.id, exam_id)

@router.post("/exam-attempts/{attempt_id}/submit", response_model=UserExamAttemptResponse)
def submit_exam_attempt_route(
    attempt_id: int,
    answers_data: ExamAnswersRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return submit_exam_attempt(db, current_user.id, attempt_id, answers_data.answers)

@router.get("/exams/{exam_id}/attempts", response_model=List[UserExamAttemptResponse])
def get_user_exam_attempts_route(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_exam_attempts(db, current_user.id, exam_id)
