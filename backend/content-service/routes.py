from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import services
import schemas
from database import get_db

router = APIRouter()

@router.get("/modules", response_model=List[schemas.Module])
def get_modules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    modules = services.get_modules(db, skip=skip, limit=limit)
    return modules

@router.get("/modules/{module_id}", response_model=schemas.Module)
def get_module(module_id: str, db: Session = Depends(get_db)):
    module = services.get_module(db, module_id=module_id)
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@router.get("/modules/{module_id}/lessons", response_model=List[schemas.Lesson])
def get_lessons(module_id: str, db: Session = Depends(get_db)):
    module = services.get_module(db, module_id=module_id)
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")

    lessons = services.get_lessons(db, module_id=module_id)
    return lessons

@router.get("/lessons/{lesson_id}", response_model=schemas.Lesson)
def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    lesson = services.get_lesson(db, lesson_id=lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson

@router.get("/lessons/{lesson_id}/exercises", response_model=List[schemas.Exercise])
def get_exercises(lesson_id: str, db: Session = Depends(get_db)):
    lesson = services.get_lesson(db, lesson_id=lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    exercises = services.get_exercises(db, lesson_id=lesson_id)
    return exercises

@router.get("/exercises/{exercise_id}", response_model=schemas.Exercise)
def get_exercise(exercise_id: str, db: Session = Depends(get_db)):
    exercise = services.get_exercise(db, exercise_id=exercise_id)
    if exercise is None:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise

@router.post("/modules", response_model=schemas.Module)
def create_module(module: schemas.ModuleCreate, db: Session = Depends(get_db)):
    return services.create_module(db=db, module=module)

@router.post("/lessons", response_model=schemas.Lesson)
def create_lesson(lesson: schemas.LessonCreate, db: Session = Depends(get_db)):
    return services.create_lesson(db=db, lesson=lesson)

@router.post("/exercises", response_model=schemas.Exercise)
def create_exercise(exercise: schemas.ExerciseCreate, db: Session = Depends(get_db)):
    return services.create_exercise(db=db, exercise=exercise)
