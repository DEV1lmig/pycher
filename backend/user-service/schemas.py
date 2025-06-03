from pydantic import BaseModel, EmailStr, validator, Field, computed_field # Add computed_field
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

ALLOWED_DOMAINS = {"gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "urbe.edu.ve"}

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=32, pattern=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$")
    last_name: str = Field(..., min_length=2, max_length=32, pattern=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$")
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: EmailStr
    password: str
    accept_terms: bool

    @validator("email")
    def email_domain_allowed(cls, v):
        domain = v.split("@")[1].lower()
        if domain not in ALLOWED_DOMAINS:
            raise ValueError("Dominio de correo no permitido")
        return v

    @validator("password")
    def password_strength(cls, v):
        if (len(v) < 8 or len(v) > 64 or
            not re.search(r"[A-Z]", v) or
            not re.search(r"[a-z]", v) or
            not re.search(r"\d", v) or
            not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v)):
            raise ValueError("La contraseña debe tener entre 8 y 64 caracteres, mayúsculas, minúsculas, número y símbolo")
        return v

    @validator("accept_terms")
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError("Debes aceptar los términos")
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime  # Add this field

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ProgressBase(BaseModel):
    module_id: str
    lesson_id: str
    completed: bool = False

class ProgressCreate(ProgressBase):
    pass

class ProgressResponse(ProgressBase):
    id: int
    user_id: int
    completion_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class ModuleProgress(BaseModel):
    module_id: str
    completed_lessons: int
    total_lessons: int
    percentage: float

# Add these schemas

class PasswordResetRequest(BaseModel):
    email: str

class PasswordReset(BaseModel):
    token: str
    new_password: str

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.@-]+$")
    password: str = Field(..., min_length=8, max_length=64)

# --- New Progress Tracking Schemas ---

# Request Schemas
class LessonStartRequest(BaseModel):
    lesson_id: int

class ExerciseCompletionRequest(BaseModel):
    submitted_code: str
    input_data: Optional[str] = None  # Optional input data for the exercise
    # is_correct: bool # Remove this, it will be determined by the backend
    # output: Optional[str] = None # Remove this, it will be determined by the backend

# Response Schemas for individual progress items
class UserLessonProgressBase(BaseModel):
    lesson_id: int
    module_id: int
    is_started: bool = False
    is_completed: bool = False
    is_unlocked: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    time_spent_minutes: Optional[int] = Field(default=0)

class UserLessonProgressResponse(UserLessonProgressBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class UserModuleProgressBase(BaseModel):
    module_id: int
    course_id: int
    is_started: bool = False
    is_completed: bool = False
    is_unlocked: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_lesson_id: Optional[int] = None
    progress_percentage: Optional[float] = Field(default=0.0)

class UserModuleProgressResponse(UserModuleProgressBase):
    id: int
    user_id: int
    lessons_progress: Optional[List[UserLessonProgressResponse]] = [] # Optional: to nest lesson details

    class Config:
        from_attributes = True

class UserCourseProgressBase(BaseModel):
    course_id: int
    is_started: bool = False
    is_completed: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_module_id: Optional[int] = None
    progress_percentage: Optional[float] = Field(default=0.0)
    total_time_spent_minutes: Optional[int] = Field(default=0)

class UserCourseProgressResponse(UserCourseProgressBase):
    id: int
    user_id: int
    modules_progress: Optional[List[UserModuleProgressResponse]] = [] # Optional: to nest module details

    class Config:
        from_attributes = True

class UserExerciseSubmissionResponse(BaseModel):
    id: int
    user_id: int
    exercise_id: int
    lesson_id: int
    submitted_code: Optional[str] = None
    is_correct: bool
    output: Optional[str] = None
    attempt_number: int
    submitted_at: datetime
    score: Optional[int] = None
    execution_time_ms: Optional[int] = None

    class Config:
        from_attributes = True

# Schema for displaying exercise progress within a lesson context
class ExerciseProgressInfo(BaseModel):
    exercise_id: int
    title: str  # Added title
    is_correct: Optional[bool] = None
    attempts: int = 0
    last_submitted_at: Optional[datetime] = None
    # score: Optional[int] = None # Uncomment if you track score per exercise submission and want to show it here

    class Config:
        from_attributes = True


# Schemas for specific endpoint responses
class LastAccessedProgressResponse(BaseModel):
    course_id: Optional[int] = None
    module_id: Optional[int] = None
    lesson_id: Optional[int] = None
    # Optional: add titles or slugs for easier frontend display
    # course_title: Optional[str] = None
    # module_title: Optional[str] = None
    # lesson_title: Optional[str] = None

class UnlockedContentResponse(BaseModel):
    unlocked_ids: List[int]

class CourseProgressDetailResponse(BaseModel):
    course_progress: Optional[UserCourseProgressResponse] = None
    modules_progress: List[UserModuleProgressResponse] = []
    # You might want to include a list of all lessons with their status too
    # all_lessons_status: List[UserLessonProgressResponse] = []

# Schemas for Exams
class CourseExamSchema(BaseModel):
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    passing_score: int
    time_limit_minutes: Optional[int] = None
    # questions: List[QuestionSchema] # Define QuestionSchema if needed

    class Config:
        from_attributes = True

class UserExamAttemptBase(BaseModel):
    exam_id: int
    course_id: int
    score: Optional[int] = Field(default=0)
    is_passed: bool = False
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    time_spent_minutes: Optional[int] = Field(default=0)
    # answers: Optional[dict] = None # Or a more structured schema

class UserExamAttemptResponse(UserExamAttemptBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

# --- Schemas that were missing or need to be explicitly defined for routes.py ---

class AnswerSubmissionSchema(BaseModel):
    question_id: int # Or str, depending on your Question model
    answer: str # Or int, List[str], etc., depending on answer format

class ExamAnswersRequest(BaseModel):
    answers: List[AnswerSubmissionSchema]

class CourseProgressSummaryResponse(BaseModel):
    course_id: int
    user_id: int
    completed_lessons: int
    total_lessons: int
    completed_exercises: int
    total_exercises: int
    progress_percentage: float
    is_course_completed: bool # Renamed from is_course_completed for consistency
    last_accessed: Optional[datetime] = None
    last_accessed_module_id: Optional[int] = None
    last_accessed_lesson_id: Optional[int] = None

    class Config:
        from_attributes = True # If you create this from a model instance or dict that needs it

class UserEnrollmentWithProgressResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    # course_title: str # Remove direct field
    # course_description: Optional[str] = None # Remove direct field
    enrollment_date: datetime
    last_accessed: Optional[datetime] = None
    is_completed: bool = False
    progress_percentage: float = 0.0
    total_time_spent_minutes: int = 0
    last_accessed_module_id: Optional[int] = None
    last_accessed_lesson_id: Optional[int] = None

    # This assumes UserCourseEnrollment instance passed to it has 'course' eager loaded
    @computed_field
    @property
    def course_title(self) -> str:
        if hasattr(self, 'course') and self.course: # self here is the UserCourseEnrollment instance
            return self.course.title
        return "Unknown Course Title" # Or raise an error, or return Optional[str]

    @computed_field
    @property
    def course_description(self) -> Optional[str]:
        if hasattr(self, 'course') and self.course:
            return self.course.description
        return None

    class Config:
        from_attributes = True

# Add this schema for user updates

class UserUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=32, pattern=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$")
    last_name: Optional[str] = Field(None, min_length=2, max_length=32, pattern=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$")
    email: Optional[EmailStr] = None

    @validator("email")
    def email_domain_allowed(cls, v):
        if v is not None:
            domain = v.split("@")[1].lower()
            if domain not in ALLOWED_DOMAINS:
                raise ValueError("Dominio de correo no permitido")
        return v

class ExerciseProgressInfo(BaseModel):
    exercise_id: int
    title: str  # Added title
    is_correct: Optional[bool] = None
    attempts: int = 0
    last_submitted_at: Optional[datetime] = None
    # score: Optional[int] = None # Uncomment if you track score per exercise submission and want to show it here

    class Config:
        from_attributes = True

class LessonProgressDetailResponse(BaseModel):
    lesson_id: int
    is_completed: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exercises_progress: List[ExerciseProgressInfo] # Expects a list of ExerciseProgressInfo

    class Config:
        from_attributes = True

from typing import List, Optional # Ensure List and Optional are imported
from datetime import datetime # Ensure datetime is imported

# Add these new schemas for the PDF report

class ReportExerciseProgressSchema(BaseModel):
    title: str
    is_correct: Optional[bool] = None
    attempts: Optional[int] = None
    score: Optional[float] = None # Changed to float to accommodate potential non-integer scores
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReportLessonProgressSchema(BaseModel):
    title: str
    is_completed: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    exercises: List[ReportExerciseProgressSchema] = []

    class Config:
        from_attributes = True

class ReportModuleProgressSchema(BaseModel):
    title: str
    is_completed: bool
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    lessons: List[ReportLessonProgressSchema] = []

    class Config:
        from_attributes = True

class ReportExamAttemptSchema(BaseModel):
    title: str # Exam title
    score: Optional[float] = None
    passed: Optional[bool] = None
    completed_at: Optional[datetime] = None
    # You might want to add exam_id if needed for linking or other purposes
    # exam_id: int

    class Config:
        from_attributes = True

class ReportCourseProgressSchema(BaseModel):
    title: str
    enrollment_date: datetime
    is_completed: bool
    progress_percentage: float
    modules: List[ReportModuleProgressSchema] = []
    exams: List[ReportExamAttemptSchema] = []
    # You might want to add course_id if needed
    # course_id: int

    class Config:
        from_attributes = True

class UserProgressReportDataSchema(BaseModel):
    user_id: int
    username: str
    email: str # Assuming email is available on your User model/schema
    first_name: Optional[str] = None # Added optional first_name
    last_name: Optional[str] = None  # Added optional last_name
    report_generated_at: datetime
    courses: List[ReportCourseProgressSchema] = []

    class Config:
        from_attributes = True
