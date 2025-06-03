from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

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
    duration_minutes: Optional[int] = None

class ModuleCreate(ModuleBase):
    pass

class Module(ModuleBase):
    lesson_count: Optional[int] = 0

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
