import logging
import re
from typing import Dict, List, Optional, Union
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm  # Add this import
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import os # For path manipulation
from datetime import datetime as dt # Alias for clari

from database import get_db
from jose import jwt, JWTError

# Import models from your proxy
from models import User, UserCourseEnrollment, UserModuleProgress, UserLessonProgress, UserExerciseSubmission, CourseExam, UserExamAttempt

from schemas import (
    UserCreate, UserResponse, Token, UserLogin,
    UserCourseProgressResponse,
    UserModuleProgressResponse,
    UserLessonProgressResponse, # Ensure this is imported
    ExerciseCompletionRequest,
    UserExerciseSubmissionResponse,
    UserExamAttemptResponse,
    ExamAnswersRequest,
    LastAccessedProgressResponse,
    CourseProgressSummaryResponse,
    UserEnrollmentWithProgressResponse,
    CourseExamSchema,
    LessonProgressDetailResponse # Add this import
)

from services import (
    get_user, get_user_by_username, get_user_by_email, create_user, authenticate_user,
    enroll_user_in_course, start_lesson, complete_exercise, get_last_accessed_progress,
    get_course_progress_summary, get_user_enrollments_with_progress, unenroll_user_from_course, # Add this import
    get_user_lesson_progress_detail, get_user_progress_report_data
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

@router.delete("/courses/{course_id}/unenroll", status_code=status.HTTP_204_NO_CONTENT)
def unenroll_from_course_route(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unenrolls the current user from the specified course and deletes all their progress.
    """
    logger.info(f"Unenrollment attempt - User ID: {current_user.id}, Course ID: {course_id}")
    unenroll_user_from_course(db=db, user_id=current_user.id, course_id=course_id)
    logger.info(f"User ID: {current_user.id} successfully unenrolled from Course ID: {course_id}")
    # FastAPI will automatically return 204 No Content for a None response with this status code
    return

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

@router.post("/lessons/{lesson_id}/start", response_model=UserLessonProgressResponse) # Changed UserLessonProgressSchema to UserLessonProgressResponse
def start_lesson_route(
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marks a lesson as started for the current user.
    """
    return start_lesson(db, current_user.id, lesson_id)

@router.post("/lessons/{lesson_id}/complete", response_model=UserLessonProgressResponse)
def complete_lesson_route(
    lesson_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return complete_lesson(db, current_user.id, lesson_id)

@router.get("/lessons/{lesson_id}/progress", response_model=LessonProgressDetailResponse)
def get_lesson_progress_route( # Changed function name to avoid conflict if you had another
    lesson_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed progress for a specific lesson for the current user.
    """
    progress_detail = get_user_lesson_progress_detail(db, current_user.id, lesson_id)
    if progress_detail is None: # Should be handled by service returning a default structure or raising 404
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson progress not found or lesson not started.")
    return progress_detail

@router.post("/exercises/{exercise_id}/submit", response_model=UserExerciseSubmissionResponse)
def submit_exercise_route(
    exercise_id: int,
    submission_data: ExerciseCompletionRequest, # Uses the updated schema
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Call the updated service function.
    # `is_correct` and `output` are no longer passed from here.
    # The service function `complete_exercise` now handles execution and evaluation.
    return complete_exercise( # Or the new name if you refactored it
        db, current_user.id, exercise_id,
        submission_data.submitted_code
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

# --- Report Routes ---

# Jinja2 and WeasyPrint
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration # For potential font configuration

# Logger setup (use your existing logger or a standard one)
logger = logging.getLogger(__name__)
if not logger.hasHandlers(): # Basic config if no handlers are set
    logging.basicConfig(level=logging.INFO)


# --- Jinja2 Environment Setup ---
# Construct the path to the templates directory relative to this file's location.
# This assumes routes.py is directly inside 'user-service' or a subdirectory of it,
# and 'templates' is a sibling to 'user-service's root or directly inside 'user-service'.

# Path to the directory containing this 'routes.py' file
_current_file_dir = os.path.dirname(os.path.abspath(__file__))

# Path to the 'user-service' directory (assuming routes.py is inside user-service or a subfolder)
# This might need adjustment based on your exact structure.
# If routes.py is at c:\Users\dev1mig\Documents\GitHub\pycher\backend\user-service\routes.py
# then _user_service_root_dir would be c:\Users\dev1mig\Documents\GitHub\pycher\backend\user-service\
_user_service_root_dir = os.path.dirname(_current_file_dir) # if routes.py is in a direct subfolder of user-service
if os.path.basename(_current_file_dir) == "user-service": # if routes.py is directly in user-service
    _user_service_root_dir = _current_file_dir

_templates_path = os.path.join(_user_service_root_dir, "templates")

# Fallback for common Docker structure where WORKDIR is /app and user-service code is in /app
if not os.path.isdir(_templates_path) and os.path.isdir("/app/templates"):
    _templates_path = "/app/templates"
elif not os.path.isdir(_templates_path):
    # If still not found, default to "templates" relative to CWD (less robust)
    _templates_path = "templates"
    logger.warning(f"Jinja2 templates path fell back to relative 'templates'. Resolved to: {os.path.abspath(_templates_path)}")


jinja_env = None
try:
    if os.path.isdir(_templates_path):
        logger.info(f"Initializing Jinja2 Environment with template path: {_templates_path}")
        jinja_env = Environment(
            loader=FileSystemLoader(_templates_path),
            autoescape=select_autoescape(['html', 'xml'])
        )
    else:
        logger.error(f"Jinja2 templates directory not found at expected path: {_templates_path}. PDF report generation will fail.")
except Exception as e:
    logger.error(f"Failed to initialize Jinja2 Environment from path '{_templates_path}': {e}. PDF report generation will fail.", exc_info=True)
    jinja_env = None # Ensure it's None if setup fails

@router.get(
    "/me/progress/report/pdf",
    response_class=StreamingResponse,
    summary="Download User Progress Report as PDF",
    tags=["users", "reports"]
)
async def get_my_progress_report_pdf_route(
    db: Session = Depends(get_db), # Ensure get_db is correctly imported/defined
    current_user: UserResponse = Depends(get_current_user) # Ensure get_current_user and UserResponse are correct
):
    if jinja_env is None:
        logger.error(f"Jinja2 environment not initialized. Cannot generate PDF report for user {current_user.id if current_user else 'unknown'}.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server template engine not configured. Cannot generate report.")

    if not current_user or not hasattr(current_user, 'id'):
        logger.error("Could not identify current user for PDF report generation.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not identify user.")

    try:
        logger.info(f"Generating progress report PDF for user_id: {current_user.id}")

        # 1. Get data from the service
        report_data_obj = get_user_progress_report_data(db, current_user.id)

        # 2. Convert Pydantic model to dict for Jinja2. `model_dump` is for Pydantic V2.
        report_data_dict = report_data_obj.model_dump(mode='python') # mode='python' keeps datetime objects as datetime

        # 3. Render HTML template
        template = jinja_env.get_template("progress_report.html")
        html_content = template.render(report_data=report_data_dict)
        logger.debug(f"HTML content for PDF generated for user_id: {current_user.id}")

        # 4. Convert HTML to PDF using WeasyPrint
        pdf_file_stream = io.BytesIO()

        # Optional: Configure fonts if needed, e.g., for non-Latin characters or custom fonts
        # font_config = FontConfiguration()
        # HTML(string=html_content, font_config=font_config).write_pdf(pdf_file_stream)

        HTML(string=html_content).write_pdf(pdf_file_stream)
        pdf_file_stream.seek(0) # Reset stream position to the beginning

        logger.info(f"PDF generated successfully for user_id: {current_user.id}")

        # 5. Return StreamingResponse
        username_for_file = "".join(c if c.isalnum() else "_" for c in current_user.username) # Sanitize username
        filename_date = dt.utcnow().strftime("%Y%m%d")
        filename = f"Pycher_Progress_Report_{username_for_file}_{filename_date}.pdf"

        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        return StreamingResponse(pdf_file_stream, media_type="application/pdf", headers=headers)

    except HTTPException as e:
        # Re-raise HTTPExceptions that might come from the service layer (e.g., User Not Found)
        logger.error(f"HTTPException while generating PDF report for user {current_user.id}: {e.detail}", exc_info=True)
        raise e
    except Exception as e:
        logger.error(f"Unexpected error generating PDF report for user {current_user.id}: {str(e)}", exc_info=True)
        # Log the full traceback for unexpected errors
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Could not generate PDF report due to an internal server error.")

# Ensure your router is included in your main FastAPI app
# e.g., app.include_router(router)
