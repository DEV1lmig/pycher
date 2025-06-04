from http.client import HTTPException
from sqlalchemy.orm import Session, joinedload, selectinload
from fastapi import Request, Depends
from sqlalchemy import func
from typing import Optional, Dict, List, Any # Ensure Dict and List are imported
import models # Assuming your models are in models.py (e.g., models.Lesson, models.Module, models.Course)
import schemas # Assuming your Pydantic schemas are in schemas.py
import redis
import os
from jose import jwt, JWTError
import json
import httpx # ADDED for async HTTP calls
from models import (
    Module, Lesson, Exercise, Course, UserCourseEnrollment, CourseRating,
    User, UserModuleProgress, UserLessonProgress  # <-- Add these
)
from schemas import ModuleCreate, LessonCreate, ExerciseCreate
import logging
import hashlib # For creating cache keys from lists of IDs

# Redis client for caching
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = os.getenv("REDIS_PORT", 6379)
redis_user = os.getenv("REDIS_USER", None)
redis_password = os.getenv("REDIS_PASSWORD", None)
redis_client = redis.Redis(host=redis_host, username=redis_user, password=redis_password, port=redis_port, decode_responses=True)
CACHE_TTL = 3600  # 1 hour

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # Use the same key as user-service
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Use the same algorithm as user-service

# Environment variable for user-service URL
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8000/api/v1/users") # Ensure this is the correct base path

logger = logging.getLogger(__name__) # Use the existing logger or the one from the top

# --- Helper for creating cache keys for batch requests ---
def _create_batch_cache_key(user_id: int, item_type: str, ids: List[int]) -> str:
    if not ids:
        return f"user:{user_id}:batch_{item_type}_progress:empty"
    # Sort IDs to ensure cache key consistency regardless of input order
    sorted_ids_str = ",".join(map(str, sorted(list(set(ids))))) # Ensure unique, sorted IDs
    ids_hash = hashlib.md5(sorted_ids_str.encode()).hexdigest()
    return f"user:{user_id}:batch_{item_type}_progress:{ids_hash}"

# --- New Batch Fetching Functions (internal to content-service) ---
async def _fetch_batch_module_progress(
    user_id: int, token: str, module_ids: List[int], client: httpx.AsyncClient
) -> Dict[int, bool]:
    if not module_ids:
        return {}

    cache_key = _create_batch_cache_key(user_id, "module", module_ids)
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.debug(f"Cache HIT for batch module progress: {cache_key}")
            return json.loads(cached_data)
    except Exception as e:
        logger.error(f"Redis GET error for {cache_key}: {e}")

    logger.debug(f"Cache MISS for batch module progress: {cache_key}. Fetching from user-service.")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"module_ids": module_ids}
    progress_map = {}
    try:
        resp = await client.post(f"{USER_SERVICE_URL}/modules/progress/batch", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        progress_map = {int(k): v for k, v in data.get("progress", {}).items()} # Ensure keys are int
        try:
            redis_client.setex(cache_key, CACHE_TTL, json.dumps(progress_map))
        except Exception as e:
            logger.error(f"Redis SETEX error for {cache_key}: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching batch module progress for U{user_id}, M_IDs {module_ids}: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Unexpected error fetching batch module progress for U{user_id}, M_IDs {module_ids}: {e}", exc_info=True)

    return progress_map

async def _fetch_batch_lesson_progress(
    user_id: int, token: str, lesson_ids: List[int], client: httpx.AsyncClient
) -> Dict[int, bool]:
    if not lesson_ids:
        return {}

    cache_key = _create_batch_cache_key(user_id, "lesson", lesson_ids)
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.debug(f"Cache HIT for batch lesson progress: {cache_key}")
            return json.loads(cached_data)
    except Exception as e:
        logger.error(f"Redis GET error for {cache_key}: {e}")

    logger.debug(f"Cache MISS for batch lesson progress: {cache_key}. Fetching from user-service.")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"lesson_ids": lesson_ids}
    progress_map = {}
    try:
        resp = await client.post(f"{USER_SERVICE_URL}/lessons/progress/batch", json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        progress_map = {int(k): v for k, v in data.get("progress", {}).items()} # Ensure keys are int
        try:
            redis_client.setex(cache_key, CACHE_TTL, json.dumps(progress_map))
        except Exception as e:
            logger.error(f"Redis SETEX error for {cache_key}: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching batch lesson progress for U{user_id}, L_IDs {lesson_ids}: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Unexpected error fetching batch lesson progress for U{user_id}, L_IDs {lesson_ids}: {e}", exc_info=True)

    return progress_map

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
        "validation_type": exercise.validation_type,
        "validation_rules": exercise.validation_rules,
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

def get_next_lesson_info(db: Session, current_lesson_id: int) -> Optional[Dict]:
    """
    Determines the next lesson, which could be in the current module or the next module.
    Returns a dictionary with 'id', 'title', 'module_id', and 'module_title' of the next lesson,
    or None if no next lesson exists.
    """
    current_lesson = db.query(models.Lesson).options(
        joinedload(models.Lesson.module).joinedload(models.Module.course) # Eager load module and course
    ).filter(models.Lesson.id == current_lesson_id).first()

    if not current_lesson or not current_lesson.module or not current_lesson.module.course_id:
        # Current lesson, its module, or course context is missing
        return None

    current_module = current_lesson.module
    current_course_id = current_lesson.module.course_id

    # 1. Try to find the next lesson in the current module
    lessons_in_current_module = db.query(models.Lesson).filter(
        models.Lesson.module_id == current_module.id,
        models.Lesson.order_index > current_lesson.order_index
    ).order_by(models.Lesson.order_index.asc()).all()

    if lessons_in_current_module:
        next_l = lessons_in_current_module[0]
        return {
            "id": next_l.id,
            "title": next_l.title,
            "module_id": current_module.id,
            "module_title": current_module.title
        }

    # 2. If no next lesson in current module, try to find the first lesson of the next module in the same course
    modules_in_course = db.query(models.Module).filter(
        models.Module.course_id == current_course_id,
        models.Module.order_index > current_module.order_index
    ).order_by(models.Module.order_index.asc()).all()

    if modules_in_course:
        next_module_candidate = modules_in_course[0]
        # Find the first lesson in this next module candidate
        first_lesson_in_next_module = db.query(models.Lesson).filter(
            models.Lesson.module_id == next_module_candidate.id
        ).order_by(models.Lesson.order_index.asc()).first()

        if first_lesson_in_next_module:
            return {
                "id": first_lesson_in_next_module.id,
                "title": first_lesson_in_next_module.title,
                "module_id": next_module_candidate.id,
                "module_title": next_module_candidate.title
            }

    # 3. No next lesson found in the current module or any subsequent module in the course
    return None

async def get_lessons_with_lock_status(db: Session, module_id: int, user_id: int, token: str) -> List[schemas.LessonSchema]:
    """
    Fetches lessons for a module, determines their lock status based on predecessor completion.
    Assumes Lesson model has 'is_active' and 'order_index'.
    """
    # Removed caching for user-specific lock status
    db_lessons = db.query(models.Lesson).filter(
        models.Lesson.module_id == module_id,
        models.Lesson.is_active == True # Assuming an is_active flag
    ).order_by(models.Lesson.order_index).all()

    processed_lessons = []
    previous_lesson_completed = True # First lesson is implicitly unlocked

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        for i, lesson_db_model in enumerate(db_lessons):
            current_lesson_locked = False
            if i > 0: # Not the first lesson
                predecessor_lesson_id = db_lessons[i-1].id
                try:
                    resp = await client.get(f"{USER_SERVICE_URL}/lessons/{predecessor_lesson_id}/progress", headers=headers)
                    resp.raise_for_status()
                    progress_data = resp.json()
                    previous_lesson_completed = progress_data.get("is_completed", False)
                    logger.debug(f"U{user_id} M{module_id} L{lesson_db_model.id}: Predecessor L{predecessor_lesson_id} completed: {previous_lesson_completed}")
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error fetching lesson progress for L{predecessor_lesson_id} U{user_id}: {e.response.status_code} - {e.response.text}")
                    previous_lesson_completed = False
                except Exception as e:
                    logger.error(f"Unexpected error fetching lesson progress for L{predecessor_lesson_id} U{user_id}: {e}", exc_info=True)
                    previous_lesson_completed = False
                current_lesson_locked = not previous_lesson_completed

            lesson_schema_instance = schemas.LessonSchema.from_orm(lesson_db_model)
            lesson_schema_instance.is_locked = current_lesson_locked
            # If lessons have exercises and those need lock status, a similar nested call would be here.
            # lesson_schema_instance.exercises = await get_exercises_with_lock_status(...)
            processed_lessons.append(lesson_schema_instance)

    return processed_lessons

async def get_modules_by_course_with_lock_status(db: Session, course_id: int, user_id: int, token: str) -> List[schemas.ModuleSchema]:
    """
    Fetches modules for a course, determines their lock status, and includes lessons with their lock status.
    Assumes Module model has 'is_active' and 'order_index'.
    """
    # Removed caching for user-specific lock status
    db_modules = db.query(models.Module).filter(
        models.Module.course_id == course_id,
        models.Module.is_active == True # Assuming an is_active flag
    ).order_by(models.Module.order_index).all() # Ensure your Module model has 'order_index'

    processed_modules = []
    previous_module_completed = True # First module is implicitly unlocked

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"Bearer {token}"}
        for i, module_db_model in enumerate(db_modules):
            current_module_locked = False
            if i > 0: # Not the first module
                predecessor_module_id = db_modules[i-1].id
                try:
                    resp = await client.get(f"{USER_SERVICE_URL}/modules/{predecessor_module_id}/progress", headers=headers)
                    resp.raise_for_status()
                    progress_data = resp.json()
                    previous_module_completed = progress_data.get("is_completed", False)
                    logger.debug(f"U{user_id} C{course_id} M{module_db_model.id}: Predecessor M{predecessor_module_id} completed: {previous_module_completed}")
                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error fetching module progress for M{predecessor_module_id} U{user_id}: {e.response.status_code} - {e.response.text}")
                    previous_module_completed = False
                except Exception as e:
                    logger.error(f"Unexpected error fetching module progress for M{predecessor_module_id} U{user_id}: {e}", exc_info=True)
                    previous_module_completed = False
                current_module_locked = not previous_module_completed

            lessons_for_this_module = await get_lessons_with_lock_status(db, module_db_model.id, user_id, token)

            module_schema_instance = schemas.ModuleSchema.from_orm(module_db_model)
            module_schema_instance.is_locked = current_module_locked
            module_schema_instance.lessons = lessons_for_this_module
            module_schema_instance.lesson_count = len(lessons_for_this_module) # Update count based on fetched lessons
            processed_modules.append(module_schema_instance)

    return processed_modules

# You might need a new top-level service function for fetching full course details with locked modules/lessons
async def get_course_details_with_lock_status(db: Session, course_id: int, user_id: int, token: str) -> Optional[schemas.CourseSchema]:
    db_course = db.query(models.Course).filter(models.Course.id == course_id, models.Course.is_active == True).first()
    if not db_course:
        return None

    # Here, you could implement course-level prerequisite checks if needed, setting db_course.is_locked
    # For now, assuming courses are not locked by other courses.

    modules_with_status = await get_modules_by_course_with_lock_status(db, course_id, user_id, token)

    course_schema_instance = schemas.CourseSchema.from_orm(db_course)
    course_schema_instance.modules = modules_with_status
    # course_schema_instance.is_locked = db_course.is_locked # If course lock status is determined

    return course_schema_instance


# --- Replace or Update existing service functions that are called by routes ---
# For example, if your route for getting modules of a course calls `get_modules_by_course`,
# that route now needs to be async and call `get_modules_by_course_with_lock_status`.
# The original `get_modules_by_course` might be kept for admin purposes or internal use
# if a version without lock status is needed.

# The existing `get_lessons` function (which fetches lessons for a module)
# should be replaced or augmented by `get_lessons_with_lock_status` when called by a route
# that needs to show lock status.

# Remove or adapt caching for functions that now return user-specific data:
# - get_modules_by_course (if it's replaced by the async version for user views)
# - get_lessons (if it's replaced by the async version for user views)

# Example: The old get_lessons might be:
# def get_lessons(db: Session, module_id: str): ...
# This would be called by a route that now needs user context.

# The function `get_module_progress` (lines 303-325) seems to be calculating module progress
# within content-service. This logic is more appropriate for user-service.
# Content-service will *query* user-service for module completion.
# I will comment out this function for now to avoid confusion, as its role is superseded.
# def get_module_progress(db: Session, user_id: int, module_id: int) -> Optional[Dict[str, Any]]:
#     # Get the progress of a user in a specific module, including lesson and exercise completion.
#     # Get all lessons in the module
#     lessons = db.query(Lesson).filter(Lesson.module_id == module_id).all()
#
#     total_lessons = len(lessons)
#     if total_lessons == 0:
#         return {
#             "module_id": module_id,
#             "completed_lessons": 0,
#             "total_lessons": 0,
#             "progress_percentage": 0.0
#         }
#
#     # Get completed lessons for the user in this module
#     completed_lessons = db.query(Lesson).join(UserCourseEnrollment).filter(
#         Lesson.module_id == module_id,
#         UserCourseEnrollment.user_id == user_id,
#         UserCourseEnrollment.progress >= 100
#     ).all()
#
#     completed_lessons_count = len(completed_lessons)
#
#     return {
#         "module_id": module_id,
#         "completed_lessons": completed_lessons_count,
#         "total_lessons": total_lessons,
#         "progress_percentage": (completed_lessons_count / total_lessons) * 100.0
#     }

async def get_user_context(request: Request) -> dict:
    """
    Extract user_id and token from Authorization header (JWT or similar).
    Returns a dict with user_id and token, or None if not authenticated.
    """
    auth_header = request.headers.get("Authorization")
    token = None
    user_id = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("user_id")
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return {"user_id": user_id, "token": token}
