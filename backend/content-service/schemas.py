from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# Exercise schemas
class ExerciseBase(BaseModel):
    id: str
    title: str
    lesson_id: str
    order: int
    description: str
    starter_code: str
    solution_code: str
    test_code: Optional[str] = None
    hints: Optional[List[str]] = None

class ExerciseCreate(ExerciseBase):
    pass

class Exercise(ExerciseBase):
    class Config:
        from_attributes = True

# Lesson schemas
class LessonBase(BaseModel):
    id: str
    title: str
    module_id: str
    order: int
    content: str
    type: str

class LessonCreate(LessonBase):
    pass

class Lesson(LessonBase):
    class Config:
        from_attributes = True

# Module schemas
class ModuleBase(BaseModel):
    id: str
    title: str
    description: str
    level: str
    order: int
    image_url: Optional[str] = None

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
