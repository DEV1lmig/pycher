import json
import os
from sqlalchemy.orm import Session as SQLAlchemySession # Renamed to avoid conflict
from sqlalchemy import create_engine, inspect, text # ADDED text
from sqlalchemy.orm import sessionmaker
import logging
import hashlib # Ensure hashlib is imported at the top
# Ensure all models that need to be cleared are imported
from models import (
    Base, Course, Module, Lesson, User, Progress, Exercise,
    UserCourseEnrollment, UserModuleProgress, UserLessonProgress,
    UserExerciseSubmission, ExamQuestion, CourseExam, UserExamAttempt # Added CourseExam
)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_DATA_DIR = os.path.join(os.path.dirname(__file__), "seed_data")
SEED_FILES_TO_TRACK = {
    "courses": "seed_courses.json",
    "modules": "seed_modules.json",
    "lessons": "seed_lessons.json",
    "exercises": "seed_exercises.json"
}
SEED_FILE_HASHES_PATH = os.path.join(os.path.dirname(__file__), ".seed_file_hashes.json")

# --- Helper Functions ---
def is_database_empty(session: SQLAlchemySession) -> bool:
    """Checks if a core table (e.g., Course) is empty to determine if DB is fresh."""
    course_count = session.query(Course).count()
    logger.info(f"Course count: {course_count}. Database empty: {course_count == 0}")
    return course_count == 0

def get_file_hash(filepath):
    """Computes SHA256 hash of a file."""
    h = hashlib.sha256()
    if not os.path.exists(filepath):
        return None # Or raise error
    with open(filepath, 'rb') as file:
        while True:
            chunk = file.read(h.block_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def get_current_seed_file_hashes():
    """Calculates current hashes for all tracked seed files."""
    current_hashes = {}
    for key, filename in SEED_FILES_TO_TRACK.items():
        filepath = os.path.join(SEED_DATA_DIR, filename)
        current_hashes[key] = get_file_hash(filepath)
    return current_hashes

def load_last_seed_file_hashes():
    """Loads the last known seed file hashes from .seed_file_hashes.json."""
    if not os.path.exists(SEED_FILE_HASHES_PATH):
        return {}
    try:
        with open(SEED_FILE_HASHES_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.warning(f"Could not decode {SEED_FILE_HASHES_PATH}. Returning empty hashes.")
        return {}
    except Exception as e:
        logger.error(f"Error loading {SEED_FILE_HASHES_PATH}: {e}", exc_info=True)
        return {}

def save_seed_file_hashes(hashes_to_save):
    """Saves the given seed file hashes to .seed_file_hashes.json."""
    try:
        with open(SEED_FILE_HASHES_PATH, 'w') as f:
            json.dump(hashes_to_save, f, indent=2)
        logger.info(f"Successfully saved seed file hashes to {SEED_FILE_HASHES_PATH}")
    except Exception as e:
        logger.error(f"Error saving {SEED_FILE_HASHES_PATH}: {e}", exc_info=True)

def get_current_migration_hash():
    # Example: read from alembic_version table or migration files
    # For now, just return the latest migration file hash or timestamp
    migrations_dir = os.path.join(os.path.dirname(__file__), "alembic/versions")
    migration_files = sorted(os.listdir(migrations_dir))
    if not migration_files:
        return None
    latest = migration_files[-1]
    with open(os.path.join(migrations_dir, latest), "rb") as f:
        import hashlib
        return hashlib.sha256(f.read()).hexdigest()

def get_last_seeded_migration_hash():
    # Store this in a file or a DB table
    hash_file = os.path.join(os.path.dirname(__file__), ".last_seeded_migration")
    if not os.path.exists(hash_file):
        return None
    with open(hash_file, "r") as f:
        return f.read().strip()

def set_last_seeded_migration_hash(hash_val):
    hash_file = os.path.join(os.path.dirname(__file__), ".last_seeded_migration")
    with open(hash_file, "w") as f:
        f.write(hash_val)

# Placeholder for future enhancements
def check_for_new_migrations_since_last_seed() -> bool:
    logger.info("Placeholder: Migration check not implemented. Returning False.")
    return False

# Placeholder for future enhancements
def check_for_json_seed_file_changes() -> bool:
    logger.info("Placeholder: JSON seed file change check not implemented. Returning False.")
    return False

# Define levels for clearing and resetting (order matters for clearing)
CLEAR_LEVEL_HIERARCHY = ["exercises", "lessons", "modules", "courses"]

TABLES_FOR_LEVEL = {
    "courses": [Course, UserCourseEnrollment],
    "modules": [Module, UserModuleProgress],
    "lessons": [Lesson, UserLessonProgress],
    "exercises": [Exercise, UserExerciseSubmission, Progress]
}

SEQUENCES_FOR_LEVEL = {
    "courses": ["courses_id_seq", "user_course_enrollments_id_seq"],
    "modules": ["modules_id_seq", "user_module_progress_id_seq"],
    "lessons": ["lessons_id_seq", "user_lesson_progress_id_seq"],
    "exercises": ["exercises_id_seq", "user_exercise_submissions_id_seq"]
}

def clear_data(session: SQLAlchemySession):
    logger.info("Clearing existing data...")
    try:
        # --- CLEAR IN CORRECT DEPENDENCY ORDER ---
        session.query(UserExerciseSubmission).delete(synchronize_session=False)
        session.query(Progress).delete(synchronize_session=False)
        session.query(UserLessonProgress).delete(synchronize_session=False)
        session.query(UserModuleProgress).delete(synchronize_session=False)
        session.query(UserCourseEnrollment).delete(synchronize_session=False)
        session.query(ExamQuestion).delete(synchronize_session=False)
        # --- ADD THIS LINE: Clear UserExamAttempt before CourseExam ---
        session.query(UserExamAttempt).delete(synchronize_session=False)
        session.query(Exercise).delete(synchronize_session=False)
        session.query(Lesson).delete(synchronize_session=False)
        session.query(Module).delete(synchronize_session=False)
        session.query(CourseExam).delete(synchronize_session=False)  # <-- Now safe to delete
        session.query(Course).delete(synchronize_session=False)
        session.commit()
        logger.info("Successfully cleared existing data.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error clearing data: {e}", exc_info=True)
        raise

def clear_data_from_level(session: SQLAlchemySession, highest_level_changed: str):
    logger.info(f"Clearing data from level '{highest_level_changed}' downwards...")
    try:
        session.query(UserExerciseSubmission).delete(synchronize_session=False)
        session.query(UserLessonProgress).delete(synchronize_session=False)
        session.query(UserModuleProgress).delete(synchronize_session=False)
        session.query(UserCourseEnrollment).delete(synchronize_session=False)
        session.query(Progress).delete(synchronize_session=False)
        session.query(ExamQuestion).delete(synchronize_session=False)
        session.query(UserExamAttempt).delete(synchronize_session=False)
        session.query(Exercise).delete(synchronize_session=False)
        session.query(Lesson).delete(synchronize_session=False)
        session.query(Module).delete(synchronize_session=False)
        session.query(CourseExam).delete(synchronize_session=False)  # <-- Now safe to delete
        session.query(Course).delete(synchronize_session=False)
        session.commit()
        logger.info("Successfully cleared all data in dependency order.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error clearing data: {e}", exc_info=True)
        raise

def reset_sequences_for_level(session: SQLAlchemySession, highest_level_changed: str):
    """Resets sequences from the specified level downwards."""
    logger.info(f"Resetting sequences from level '{highest_level_changed}' downwards...")
    sequences_to_reset_names = set()

    start_index = -1
    try:
        start_index = CLEAR_LEVEL_HIERARCHY.index(highest_level_changed)
    except ValueError:
        logger.error(f"Invalid reset level: {highest_level_changed}. Will attempt to reset all known sequences.")
        # Add all sequences if level is unknown or if it's 'courses'
        for key in SEQUENCES_FOR_LEVEL:
            sequences_to_reset_names.update(SEQUENCES_FOR_LEVEL[key])

    if start_index != -1:
         levels_for_sequence_reset = CLEAR_LEVEL_HIERARCHY[start_index:]
         for level in levels_for_sequence_reset:
             if level in SEQUENCES_FOR_LEVEL:
                 sequences_to_reset_names.update(SEQUENCES_FOR_LEVEL[level])

    # Always include user sequence if users are reseeded, but user reseeding is separate.
    # For now, let's assume users_id_seq is reset if 'courses' level is reset (full reset).
    if highest_level_changed == "courses":
         sequences_to_reset_names.add("users_id_seq")

    logger.info(f"Sequences to reset: {list(sequences_to_reset_names)}")
    if not sequences_to_reset_names:
        logger.info("No sequences identified for reset based on level.")
        return

    for seq_name in sequences_to_reset_names:
        try:
            session.execute(text(f'ALTER SEQUENCE public.{seq_name} RESTART WITH 1;'))
        except Exception as e:
            logger.warning(f"Could not reset sequence {seq_name}: {e}")
    session.commit()
    logger.info(f"PostgreSQL sequences reset for level '{highest_level_changed}'.")

def seed_courses(session: SQLAlchemySession):
    logger.info("Seeding courses...")
    with open(os.path.join(os.path.dirname(__file__), "seed_data/seed_courses.json"), encoding="utf-8") as f:
        courses_data = json.load(f)
        for course_item_data in courses_data:
            course_item_data.pop("total_modules", None)
            if not session.query(Course).filter_by(id=course_item_data["id"]).first():
                session.add(Course(**course_item_data))
        session.commit()
    logger.info("Courses seeded.")

def seed_modules(session: SQLAlchemySession):
    logger.info("Seeding modules...")
    with open(os.path.join(os.path.dirname(__file__), "seed_data/seed_modules.json"), encoding="utf-8") as f:
        modules_data = json.load(f)
        for module_item_data in modules_data:
            if not session.query(Module).filter_by(id=module_item_data["id"]).first():
                session.add(Module(**module_item_data))
        session.commit()
    logger.info("Modules seeded.")

def seed_lessons(session: SQLAlchemySession):
    logger.info("Seeding lessons...")
    with open(os.path.join(os.path.dirname(__file__), "seed_data/seed_lessons.json"), encoding="utf-8") as f:
        lessons_data = json.load(f)
        for lesson_item_data in lessons_data:
            if not session.query(Lesson).filter_by(id=lesson_item_data["id"]).first():
                session.add(Lesson(**lesson_item_data))
        session.commit()
    logger.info("Lessons seeded.")

def seed_exercises(session: SQLAlchemySession):
    logger.info("Seeding exercises...")
    with open(os.path.join(os.path.dirname(__file__), "seed_data/seed_exercises.json"), encoding="utf-8") as f:
        exercises_data = json.load(f)
        for exercise_item_data in exercises_data:
            exercise_id = exercise_item_data.get("id")
            exists = session.query(Exercise).filter_by(id=exercise_id).first() if exercise_id is not None else None

            if "module_id" in exercise_item_data and exercise_item_data["module_id"] is not None:
                if not session.query(Module).filter_by(id=exercise_item_data["module_id"]).first():
                    logger.warning(f"Module with id {exercise_item_data['module_id']} not found for exercise {exercise_item_data.get('title', exercise_id)}. Skipping.")
                    continue
            if "lesson_id" in exercise_item_data and exercise_item_data["lesson_id"] is not None:
                if not session.query(Lesson).filter_by(id=exercise_item_data["lesson_id"]).first():
                    logger.warning(f"Lesson with id {exercise_item_data['lesson_id']} not found for exercise {exercise_item_data.get('title', exercise_id)}. Skipping.")
                    continue
            if "course_id" in exercise_item_data and exercise_item_data["course_id"] is not None: # Check for course_id if exercise is linked directly
                if not session.query(Course).filter_by(id=exercise_item_data["course_id"]).first():
                    logger.warning(f"Course with id {exercise_item_data['course_id']} not found for exercise {exercise_item_data.get('title', exercise_id)}. Skipping.")
                    continue
            if not exists:
                session.add(Exercise(**exercise_item_data))
        session.commit()
    logger.info("Exercises seeded.")

def seed_users(session: SQLAlchemySession):
    logger.info("Seeding users...")
    # Example: Create a default user if none exist
    if session.query(User).count() == 0:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        default_user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password=pwd_context.hash("password"), # Replace with a secure password hashing
            is_active=True
        )
        session.add(default_user)
        session.commit()
        logger.info("Default user 'testuser' created.")
    else:
        logger.info("Users already exist. Skipping user seeding.")
    logger.info("Users seeding process complete.")


def reset_postgres_sequences(session):
    """
    Resets the auto-increment (serial/sequence) counters for all main tables to 1.
    Only works for PostgreSQL.
    """
    sequence_names = [
        "courses_id_seq",
        "modules_id_seq",
        "lessons_id_seq",
        "exercises_id_seq",
        "user_course_enrollments_id_seq",
        "user_module_progress_id_seq",
        "user_lesson_progress_id_seq",
        "user_exercise_submissions_id_seq",
        "exam_questions_id_seq",
        "user_exam_attempts_id_seq",
        "users_id_seq"
    ]
    for seq in sequence_names:
        try:
            session.execute(text(f'ALTER SEQUENCE public.{seq} RESTART WITH 1;')) # MODIFIED: Wrapped with text()
        except Exception as e:
            logger.warning(f"Could not reset sequence {seq}: {e}")
    session.commit()
    logger.info("PostgreSQL sequences reset to 1.")

def seed_course_exams(session: SQLAlchemySession):
    logger.info("Seeding course exams from exam exercises...")
    exercises_path = os.path.join(SEED_DATA_DIR, "seed_exercises.json")
    if not os.path.exists(exercises_path):
        logger.warning("seed_exercises.json not found, skipping course exam seeding.")
        return

    with open(exercises_path, encoding="utf-8") as f:
        exercises_data = json.load(f)
        # Filter only exam exercises
        exam_exercises = [
            ex for ex in exercises_data
            if ex.get("course_id") is not None
            and ex.get("module_id") is None
            and ex.get("lesson_id") is None
            and ex.get("validation_type") == "exam"
        ]
        # Sort by order_index
        exam_exercises.sort(key=lambda ex: ex.get("order_index", 0))

        for exercise in exam_exercises:
            course_id = exercise["course_id"]
            title = exercise.get("title", f"Examen Final {exercise.get('id')}")
            order_index = exercise.get("order_index", 1)

            course_exists = session.query(Course).filter_by(id=course_id).first()
            if not course_exists:
                logger.warning(f"Course with id {course_id} not found for exam '{title}'. Skipping CourseExam creation.")
                continue

            existing = session.query(CourseExam).filter_by(
                course_id=course_id,
                title=title
            ).first()

            if not existing:
                course_exam = CourseExam(
                    course_id=course_id,
                    title=title,
                    description=exercise.get("description", ""),
                    order_index=order_index,  # <-- THIS LINE seeds order_index
                    pass_threshold_percentage=70.0
                )
                session.add(course_exam)
                logger.info(f"Staged CourseExam '{title}' for course {course_id} with order_index {order_index}.")
    session.commit()
    logger.info("Course exams seeded.")

if __name__ == "__main__":
    logger.info("Starting database seeding process...")
    Base.metadata.create_all(bind=engine) # Ensure tables exist
    session = SessionLocal()

    try:
        current_migration_hash = get_current_migration_hash()
        last_seeded_migration_hash = get_last_seeded_migration_hash()
        logger.info(f"Current migration hash: {current_migration_hash}")
        logger.info(f"Last seeded migration hash: {last_seeded_migration_hash}")

        current_seed_files_hashes = get_current_seed_file_hashes()
        last_seed_files_hashes = load_last_seed_file_hashes()
        logger.info(f"Current seed file hashes: {current_seed_files_hashes}")
        logger.info(f"Last seed file hashes: {last_seed_files_hashes}")

        reseed_level = None # Will store the highest level that needs reseeding ("courses", "modules", etc.)

        if current_migration_hash != last_seeded_migration_hash:
            logger.warning("Migration change detected. Full reseed required.")
            reseed_level = "courses" # Highest level, triggers full clear and reseed
            set_last_seeded_migration_hash(current_migration_hash)
        else:
            # Check seed file changes in hierarchical order
            if current_seed_files_hashes.get("courses") != last_seed_files_hashes.get("courses"):
                logger.info("Change detected in seed_courses.json.")
                reseed_level = "courses"
            elif current_seed_files_hashes.get("modules") != last_seed_files_hashes.get("modules"):
                logger.info("Change detected in seed_modules.json.")
                reseed_level = "modules"
            elif current_seed_files_hashes.get("lessons") != last_seed_files_hashes.get("lessons"):
                logger.info("Change detected in seed_lessons.json.")
                reseed_level = "lessons"
            elif current_seed_files_hashes.get("exercises") != last_seed_files_hashes.get("exercises"):
                logger.info("Change detected in seed_exercises.json.")
                reseed_level = "exercises"

        if reseed_level:
            logger.warning(f"Reseeding data from level '{reseed_level}' due to changes.")
            clear_data_from_level(session, reseed_level)
            reset_sequences_for_level(session, reseed_level)

            if reseed_level == "courses":
                seed_courses(session)
                seed_modules(session)
                seed_lessons(session)
                seed_course_exams(session)   # <-- This must come AFTER seed_courses
                seed_exercises(session)
            elif reseed_level == "modules":
                seed_modules(session)
                seed_lessons(session)
                seed_course_exams(session)
                seed_exercises(session)
            elif reseed_level == "lessons":
                seed_lessons(session)
                seed_course_exams(session)
                seed_exercises(session)
            elif reseed_level == "exercises":
                    seed_courses(session)
                    seed_modules(session)
                    seed_lessons(session)
                    seed_course_exams(session)
                    seed_exercises(session)

            save_seed_file_hashes(current_seed_files_hashes)
            logger.info(f"Reseeding from level '{reseed_level}' complete.")
        else:
            logger.info("No migration or seed file changes detected that require a targeted reseed. Running idempotent seeders for consistency.")
            seed_courses(session)
            seed_modules(session)
            seed_lessons(session)
            seed_course_exams(session)       # <-- ADD THIS LINE
            seed_exercises(session)
    except Exception as e:
        logger.error(f"CRITICAL ERROR during seeding process: {e}", exc_info=True)
        session.rollback()
        logger.error("Seeding process failed and transaction was rolled back.")
    finally:
        session.close()
        logger.info("Database session closed.")
