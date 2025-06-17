from pydantic import BaseModel, computed_field
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Existing Schemas (ensure they are defined or adjust as needed) ---
class ExerciseSchema(BaseModel): # Renamed from Exercise for clarity if it's a Pydantic schema
    id: int
    title: str
    # Add other relevant exercise fields if they are part of lesson/module responses
    # For example: order_index: int, lesson_type: Optional[str] (if exercises can be 'lessons')
    class Config:
        from_attributes = True

class LessonSchema(BaseModel): # Renamed from Lesson for clarity
    id: int
    title: str
    module_id: int
    order_index: int
    content: Optional[str] = None # Keep if needed, or make a LessonBasicSchema
    # lesson_type: str # Add if you have different types of lessons
    # exercises: List[ExerciseSchema] = [] # If exercises are nested under lessons
    is_locked: bool = False # ADDED

    class Config:
        from_attributes = True

class ModuleSchema(BaseModel): # Renamed from Module for clarity
    id: int
    course_id: int
    title: str
    description: Optional[str] = None
    order_index: int
    # level: Optional[str] = None # From your get_modules example
    lesson_count: Optional[int] = 0 # This will be the count of lessons returned
    # image_url: Optional[str] = None # From your get_modules example
    lessons: List[LessonSchema] = [] # ADDED: To nest lessons with their lock status
    is_locked: bool = False # ADDED
    is_exam: Optional[bool] = None # ADDED: If modules can be exams

    class Config:
        from_attributes = True

class CourseSchema(BaseModel): # Renamed from Course for clarity
    id: int
    title: str
    description: Optional[str] = None
    duration_minutes: Optional[int] = None
    students_count: Optional[int] = 0
    rating: Optional[float] = None
    modules: List[ModuleSchema] = [] # ADDED: To nest modules with their lock status
    # is_locked: bool = False # ADDED: If courses themselves can be locked by prerequisites
    @computed_field
    @property
    def total_modules(self) -> int:
        return len(self.modules) if self.modules else 0
    class Config:
        from_attributes = True

# Ensure your Create schemas (ModuleCreate, LessonCreate, etc.) are separate
# and don't include these dynamic fields like is_locked or nested lists.

# Exercise schemas
class ExerciseBase(BaseModel):
    id: int
    title: str
    description: str
    instructions: Optional[str] = None
    starter_code: Optional[str] = None
    solution_code: Optional[str] = None
    test_cases: Optional[str] = None
    hints: Optional[str] = None
    lesson_id: Optional[int] = None
    module_id: Optional[int] = None
    order_index: int
    validation_type: Optional[str] = None  # e.g., "output", "dynamic", "custom"
    validation_rules: Optional[Dict[str, Any]] = None  # JSON schema or other validation rules

class ExerciseCreate(ExerciseBase):
    pass

class Exercise(ExerciseBase):
    class Config:
        from_attributes = True

# Lesson schemas
class LessonBase(BaseModel):
    title: str
    content: str
    order_index: int
    duration_minutes: Optional[int] = None
    module_id: int

class LessonCreate(LessonBase):
    pass

class Lesson(LessonBase):
    id: int

    class Config:
        from_attributes = True

# Module schemas
class ModuleBase(BaseModel):
    id: int
    course_id: int
    title: str
    description: str
    order_index: int
    is_exam: Optional[bool] = None
    duration_minutes: Optional[int] = None

class ModuleCreate(ModuleBase):
    is_exam: bool = False
    pass

class Module(ModuleBase):
    lesson_count: Optional[int] = 0
    is_exam: bool
    lessons: List[LessonSchema] = []
    class Config:
        from_attributes = True

class ModuleSummary(BaseModel):
    id: str
    title: str
    description: str
    level: str
    lesson_count: int
    image_url: Optional[str] = None

# Course schemas
class CourseBase(BaseModel):
    title: str
    description: str
    level: str
    duration_minutes: Optional[int]
    total_modules: Optional[int]
    rating: Optional[float]
    students_count: Optional[int]
    image_url: Optional[str]
    color_theme: Optional[str]
    is_active: Optional[bool] = True

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserCourseEnrollment(BaseModel):
    id: int
    user_id: int
    course_id: int
    enrollment_date: datetime
    last_accessed: Optional[datetime]
    is_completed: bool
    progress_percentage: float
    total_time_spent_minutes: int

    class Config:
        from_attributes = True

class CourseRating(BaseModel):
    id: int
    user_id: int
    course_id: int
    rating: float

    class Config:
        from_attributes = True
