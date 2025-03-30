from sqlalchemy.orm import Session
from models import Module, Lesson, Exercise
from schemas import ModuleCreate, LessonCreate, ExerciseCreate
import redis
import os
import json
from typing import List, Dict, Any, Optional

# Redis client for caching
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = os.getenv("REDIS_PORT", 6379)
redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
CACHE_TTL = 3600  # 1 hour

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
            "id": module.id,
            "title": module.title,
            "description": module.description,
            "level": module.level,
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
    lessons = db.query(Lesson).filter(Lesson.module_id == module_id).order_by(Lesson.order).all()

    lesson_list = [{
        "id": lesson.id,
        "title": lesson.title,
        "module_id": lesson.module_id,
        "order": lesson.order,
        "content": lesson.content,
        "type": lesson.type
    } for lesson in lessons]

    redis_client.setex(f"module:{module_id}:lessons", CACHE_TTL, json.dumps(lesson_list))
    return lesson_list

def get_lesson(db: Session, lesson_id: str):
    # Try to get from cache
    cached = redis_client.get(f"lesson:{lesson_id}")
    if cached:
        return json.loads(cached)

    # Get from DB if not cached
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        return None

    lesson_data = {
        "id": lesson.id,
        "title": lesson.title,
        "module_id": lesson.module_id,
        "order": lesson.order,
        "content": lesson.content,
        "type": lesson.type
    }

    redis_client.setex(f"lesson:{lesson_id}", CACHE_TTL, json.dumps(lesson_data))
    return lesson_data

def get_exercises(db: Session, lesson_id: str):
    # Try to get from cache
    cached = redis_client.get(f"lesson:{lesson_id}:exercises")
    if cached:
        return json.loads(cached)

    # Get from DB if not cached
    exercises = db.query(Exercise).filter(Exercise.lesson_id == lesson_id).order_by(Exercise.order).all()

    exercise_list = [{
        "id": exercise.id,
        "title": exercise.title,
        "lesson_id": exercise.lesson_id,
        "order": exercise.order,
        "description": exercise.description,
        "starter_code": exercise.starter_code,
        "solution_code": exercise.solution_code,
        "test_code": exercise.test_code,
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
        "order": exercise.order,
        "description": exercise.description,
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
        order=module.order,
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
        order=lesson.order,
        content=lesson.content,
        type=lesson.type
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
        order=exercise.order,
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
