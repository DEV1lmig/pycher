from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import models
from typing import List
import services
import schemas
from database import get_db
from models import Lesson
import logging

logger = logging.getLogger("content-service")

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
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = services.get_lesson(db, lesson_id)
    if not lesson:
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

@router.post("/courses", response_model=schemas.Course)
def create_course(course: schemas.CourseCreate, db: Session = Depends(get_db)):
    return services.create_course(db, course)

@router.get("/courses", response_model=List[schemas.Course])
def list_courses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return services.get_courses(db, skip, limit)

@router.get("/courses/{course_id}", response_model=schemas.Course)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = services.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.post("/courses/{course_id}/enroll", response_model=schemas.UserCourseEnrollment)
def enroll_in_course(course_id: int, user_id: int, db: Session = Depends(get_db)):
    """
    Enroll a user in a course and increment students_count.
    """
    enrollment = services.enroll_user_in_course(db, user_id=user_id, course_id=course_id)
    if not enrollment:
        raise HTTPException(status_code=400, detail="Enrollment failed")
    return enrollment

@router.post("/courses/{course_id}/unenroll", response_model=dict)
def unenroll_from_course(course_id: int, user_id: int, db: Session = Depends(get_db)):
    """
    Unenroll a user from a course and decrement students_count.
    """
    services.unenroll_user_from_course(db, user_id=user_id, course_id=course_id)
    return {"detail": "Unenrolled successfully"}

@router.post("/courses/{course_id}/rate", response_model=dict)
def rate_course(course_id: int, user_id: int, rating: float, db: Session = Depends(get_db)):
    """
    Rate a course and update its average rating.
    """
    services.rate_course(db, user_id=user_id, course_id=course_id, rating=rating)
    return {"detail": "Rating submitted"}

@router.get("/courses/{course_id}/modules", response_model=List[schemas.Module])
def get_modules_by_course(course_id: int, db: Session = Depends(get_db)):
    # Optionally check if course exists
    course = services.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    modules = services.get_modules_by_course(db, course_id)
    return modules
