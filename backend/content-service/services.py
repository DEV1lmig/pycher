from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Module, Lesson, Exercise, Course, UserCourseEnrollment, CourseRating
from schemas import ModuleCreate, LessonCreate, ExerciseCreate
import redis
import os
import json
from typing import List, Dict, Any, Optional
import logging

# Redis client for caching
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = os.getenv("REDIS_PORT", 6379)
redis_user = os.getenv("REDIS_USER", None)
redis_password = os.getenv("REDIS_PASSWORD", None)
redis_client = redis.Redis(host=redis_host, username=redis_user, password=redis_password, port=redis_port, decode_responses=True)
CACHE_TTL = 3600  # 1 hour

logger = logging.getLogger("content-service")

def get_modules(db: Session, skip: int = 0, limit: int = 100):
    # Try to get from cache
    cached = redis_client.get("modules:list")
    if cached:
        return json.loads(cached)

    # Get from DB if not cached
    modules = db.query(Module).order_by(Module.order).offset(skip).limit(limit).all()

    # Cache the result
    module_list = []
    for module in modules:
        lesson_count = db.query(Lesson).filter(Lesson.module_id == module.id).count()
        module_list.append({
            "id": modules.id,
            "title": modules.title,
            "description": modules.description,
            "level": modules.level,
            "lesson_count": lesson_count,
            "image_url": module.image_url
        })

    redis_client.setex("modules:list", CACHE_TTL, json.dumps(module_list))
    return module_list

def get_module(db: Session, module_id: str):
    # Try to get from cache
    cached = redis_client.get(f"module:{module_id}")
    if cached:
        return json.loads(cached)

    # Get from DB if not cached
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        return None

    # Don't cache the full module with lessons to save memory
    return module

def get_lessons(db: Session, module_id: str):
    # Try to get from cache
    cached = redis_client.get(f"module:{module_id}:lessons")
    if cached:
        return json.loads(cached)

    # Get from DB if not cached
    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).order_by(Lesson.order_index).all()

    lesson_list = [{
        "id": lesson.id,
        "title": lesson.title,
        "module_id": lesson.module_id,
        "order_index": lesson.order_index,
        "content": lesson.content,
    } for lesson in lessons]

    redis_client.setex(f"module:{module_id}:lessons", CACHE_TTL, json.dumps(lesson_list))
    return lesson_list

def get_lesson(db: Session, lesson_id):
    logger.info(f"Fetching lesson with id={lesson_id}")
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        logger.warning(f"Lesson {lesson_id} not found in DB")
        return None
    return lesson

def get_exercises(db: Session, lesson_id: str):
    lesson_id = int(lesson_id)  # Ensure lesson_id is an integer
    cached = redis_client.get(f"lesson:{lesson_id}:exercises")
    if cached:
        return json.loads(cached)

    # Get from DB if not cached
    exercises = db.query(Exercise).filter(Exercise.lesson_id == lesson_id).order_by(Exercise.order_index).all()

    exercise_list = [{
        "id": exercise.id,
        "title": exercise.title,
        "lesson_id": exercise.lesson_id,
        "order_index": exercise.order_index,
        "instructions": exercise.instructions,
        "description": exercise.description,
        "starter_code": exercise.starter_code,
        "solution_code": exercise.solution_code,
        "test_cases": exercise.test_cases,  # <-- fix here
        "hints": exercise.hints
    } for exercise in exercises]

    redis_client.setex(f"lesson:{lesson_id}:exercises", CACHE_TTL, json.dumps(exercise_list))
    return exercise_list

def get_exercise(db: Session, exercise_id: str):
    # Try to get from cache
    cached = redis_client.get(f"exercise:{exercise_id}")
    if cached:
        return json.loads(cached)

    # Get from DB if not cached
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        return None

    exercise_data = {
        "id": exercise.id,
        "title": exercise.title,
        "lesson_id": exercise.lesson_id,
        "order_index": exercise.order_index,
        "description": exercise.description,
        "instructions": exercise.instructions,
        "starter_code": exercise.starter_code,
        "solution_code": exercise.solution_code,
        "test_code": exercise.test_code,
        "hints": exercise.hints
    }

    redis_client.setex(f"exercise:{exercise_id}", CACHE_TTL, json.dumps(exercise_data))
    return exercise_data

def create_module(db: Session, module: ModuleCreate):
    db_module = Module(
        id=module.id,
        title=module.title,
        description=module.description,
        level=module.level,
        order_index=module.order_index,
        image_url=module.image_url
    )
    db.add(db_module)
    db.commit()
    db.refresh(db_module)

    # Invalidate cache
    redis_client.delete("modules:list")

    return db_module

def create_lesson(db: Session, lesson: LessonCreate):
    db_lesson = Lesson(
        id=lesson.id,
        title=lesson.title,
        module_id=lesson.module_id,
        order_index=lesson.order_index,
        content=lesson.content,
    )
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)

    # Invalidate cache
    redis_client.delete(f"module:{lesson.module_id}:lessons")

    return db_lesson

def create_exercise(db: Session, exercise: ExerciseCreate):
    db_exercise = Exercise(
        id=exercise.id,
        title=exercise.title,
        lesson_id=exercise.lesson_id,
        order_index=exercise.order_index,
        description=exercise.description,
        starter_code=exercise.starter_code,
        solution_code=exercise.solution_code,
        test_code=exercise.test_code,
        hints=exercise.hints
    )
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)

    # Invalidate cache
    redis_client.delete(f"lesson:{exercise.lesson_id}:exercises")

    return db_exercise

def create_course(db: Session, course_data):
    course = Course(**course_data.dict())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

def get_courses(db: Session, skip=0, limit=100):
    return db.query(Course).offset(skip).limit(limit).all()

def get_course(db: Session, course_id: int):
    return db.query(Course).filter(Course.id == course_id).first()

def enroll_user_in_course(db: Session, user_id: int, course_id: int):
    # Create enrollment
    enrollment = UserCourseEnrollment(user_id=user_id, course_id=course_id)
    db.add(enrollment)
    # Update students_count
    course = db.query(Course).filter(Course.id == course_id).first()
    if course:
        course.students_count += 1
    db.commit()
    return enrollment

def unenroll_user_from_course(db: Session, user_id: int, course_id: int):
    enrollment = db.query(UserCourseEnrollment).filter_by(user_id=user_id, course_id=course_id).first()
    if enrollment:
        db.delete(enrollment)
        course = db.query(Course).filter(Course.id == course_id).first()
        if course and course.students_count > 0:
            course.students_count -= 1
        db.commit()

def rate_course(db: Session, user_id: int, course_id: int, rating: float):
    # Add or update user's rating
    course_rating = db.query(CourseRating).filter_by(user_id=user_id, course_id=course_id).first()
    if course_rating:
        course_rating.rating = rating
    else:
        course_rating = CourseRating(user_id=user_id, course_id=course_id, rating=rating)
        db.add(course_rating)
    db.commit()
    # Recalculate average
    avg = db.query(func.avg(CourseRating.rating)).filter(CourseRating.course_id == course_id).scalar()
    course = db.query(Course).filter(Course.id == course_id).first()
    if course:
        course.rating = avg
        db.commit()

def get_modules_by_course(db: Session, course_id: int):
    return db.query(Module).filter(Module.course_id == course_id).order_by(Module.order_index).all()

def get_exercise_for_lesson(db: Session, lesson_id: int):
    return db.query(Exercise).filter(Exercise.lesson_id == lesson_id).first()

def get_module_final_exercise(db: Session, module_id: int):
    return db.query(Exercise).filter(
        Exercise.module_id == module_id,
        Exercise.lesson_id == None
    ).first()
