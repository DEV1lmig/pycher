from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import models # Ensure models is imported (e.g., from ..shared import models or similar)
from typing import List, Optional, Dict # Ensure List and Optional are imported
import services, schemas # Ensure services and schemas are imported
from database import get_db # Ensure get_db is imported
import logging
from services import get_user_context

logger = logging.getLogger("content-service")

router = APIRouter()

@router.get("/modules", response_model=List[schemas.Module])
def get_modules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    modules = services.get_modules(db, skip=skip, limit=limit)
    return modules

@router.get("/lessons/{lesson_id}/next", response_model=Optional[Dict], tags=["Lessons"])
async def get_next_lesson_route(lesson_id: int, db: Session = Depends(get_db)):
    """
    Gets information about the next lesson in sequence after the given lesson.
    Returns null if there is no next lesson in the course.
    """
    next_lesson_info = services.get_next_lesson_info(db, current_lesson_id=lesson_id)
    if not next_lesson_info:
        # It's okay to return None/null if no next lesson, not necessarily a 404 on the concept of "next"
        return None
    return next_lesson_info

@router.get("/modules/{module_id}", response_model=schemas.Module)
def get_module(module_id: str, db: Session = Depends(get_db)):
    module = services.get_module(db, module_id=module_id)
    if module is None:
        raise HTTPException(status_code=404, detail="Module not found")
    return module

@router.get("/courses/{course_id}", response_model=Optional[schemas.CourseSchema])
async def read_course_details_with_lock_status_route( # Renamed for clarity
    course_id: int,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_user_context) # Uses the auth dependency
):
    user_id = user_context.get("user_id")
    token = user_context.get("token")

    # The service function get_course_details_with_lock_status now handles user_id=None for unauthenticated
    course_details = await services.get_course_details_with_lock_status(db, course_id, user_id, token)
    if not course_details:
        raise HTTPException(status_code=404, detail="Course not found or not active")
    return course_details

@router.get("/courses/{course_id}/modules", response_model=List[schemas.ModuleSchema])
async def read_modules_for_course_with_lock_status_standalone_route( # Renamed
    course_id: int,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_user_context)
):
    user_id = user_context.get("user_id")
    token = user_context.get("token")
    # The service function now handles user_id=None for unauthenticated
    modules = await services.get_modules_by_course_with_lock_status(db, course_id, user_id, token)
    return modules

@router.get("/modules/{module_id}/lessons", response_model=List[schemas.LessonSchema])
async def read_lessons_for_module_with_lock_status_standalone_route( # Renamed
    module_id: int,
    db: Session = Depends(get_db),
    user_context: dict = Depends(get_user_context)
):
    user_id = user_context.get("user_id")
    token = user_context.get("token")
    # The service function now handles user_id=None for unauthenticated
    lessons = await services.get_lessons_with_lock_status(db, module_id, user_id, token)
    return lessons

@router.get("/lessons/{lesson_id}", response_model=schemas.Lesson)
def get_lesson_route(lesson_id: int, db: Session = Depends(get_db)):
    lesson = services.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Calculate and attach the next lesson info before returning
    next_lesson_info = services.get_next_lesson_info(db, lesson_id)

    # Pydantic will automatically pick up this attribute when creating the response
    lesson.next_lesson = next_lesson_info

    return lesson

@router.get("/lessons/{lesson_id}/exercises", response_model=List[schemas.Exercise])
def get_exercises_for_lesson_route(lesson_id: int, db: Session = Depends(get_db)):
    lesson = services.get_lesson(db, lesson_id=lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    exercises = services.get_exercises(db, lesson_id=lesson.id)
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

@router.get("/lessons/{lesson_id}/exercise", response_model=schemas.Exercise)
def get_lesson_exercise(lesson_id: int, db: Session = Depends(get_db)):
    exercise = services.get_exercise_for_lesson(db, lesson_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    return exercise

@router.get("/modules/{module_id}/final-exercise", response_model=schemas.Exercise)
def get_module_final_exercise(module_id: int, db: Session = Depends(get_db)):
    exercise = services.get_module_final_exercise(db, module_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Final exercise not found")
    return exercise

@router.get(
    "/courses/{course_id}/exam-exercises",
    response_model=List[schemas.Exercise], # Frontend expects an array
    summary="Get all exam exercises for a specific course (direct from exercise table)",
    tags=["courses", "exercises", "exams"]
)
def read_course_exam_exercises( # Renamed for clarity if needed, but name is fine
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Fetches exercises for a given course_id that are marked as exams
    by having module_id and lesson_id as NULL.
    Optionally, could also filter by validation_type == 'exam'.
    """
    exam_exercises = db.query(models.Exercise).filter(
        models.Exercise.course_id == course_id,
        models.Exercise.module_id == None,  # Check for NULL module_id
        models.Exercise.lesson_id == None,  # Check for NULL lesson_id
        # models.Exercise.validation_type == "exam" # Optional: for more specificity
    ).order_by(models.Exercise.order_index).all() # Use order_index if that's the column name

    # The frontend already handles the case where exam_exercises is an empty list.
    # if not exam_exercises:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"No direct exam exercises found for course ID {course_id} with null module/lesson IDs."
    #     )

    return exam_exercises

@router.get(
    "/courses/{course_id}/exam-random",
    response_model=schemas.Exercise,
    summary="Get a single random exam exercise for a course",
    tags=["courses", "exercises", "exams"]
)
def get_random_course_exam_route(
    course_id: int,
    db: Session = Depends(get_db)
):
    """
    Provides a single, randomly selected exam exercise for the given course.
    """
    # This now calls your modified, randomized service function
    exam_exercise = services.get_course_exam_exercise(db, course_id=course_id)
    if not exam_exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No exam exercises found for this course."
        )
    logger.info(f"Random exam exercise retrieved for course {course_id}: {exam_exercise.id}")
    return exam_exercise
