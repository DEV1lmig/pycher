import json
import os
from sqlalchemy.orm import Session as SQLAlchemySession # Renamed to avoid conflict
from sqlalchemy import create_engine, inspect, text # ADDED text
from sqlalchemy.orm import sessionmaker
import logging
import hashlib # For future JSON change detection
# Ensure all models that need to be cleared are imported
from models import (
    Base, Course, Module, Lesson, User, Progress, Exercise,
    UserCourseEnrollment, UserModuleProgress, UserLessonProgress,
    UserExerciseSubmission, CourseExam, UserExamAttempt, ExamQuestion # Added ExamQuestion
)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Helper Functions ---
def is_database_empty(session: SQLAlchemySession) -> bool:
    """Checks if a core table (e.g., Course) is empty to determine if DB is fresh."""
    course_count = session.query(Course).count()
    logger.info(f"Course count: {course_count}. Database empty: {course_count == 0}")
    return course_count == 0

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

def clear_data(session: SQLAlchemySession):
    """Deletes all data from relevant tables to allow fresh seeding."""
    logger.info("Clearing existing data...")
    try:
        # Delete in an order that respects foreign key constraints
        session.query(UserExerciseSubmission).delete(synchronize_session=False)
        session.query(Progress).delete(synchronize_session=False)
        session.query(UserLessonProgress).delete(synchronize_session=False)
        session.query(UserModuleProgress).delete(synchronize_session=False)
        session.query(UserExamAttempt).delete(synchronize_session=False)
        session.query(UserCourseEnrollment).delete(synchronize_session=False)
        session.query(ExamQuestion).delete(synchronize_session=False) # Added
        session.query(Exercise).delete(synchronize_session=False)
        session.query(Lesson).delete(synchronize_session=False)
        session.query(CourseExam).delete(synchronize_session=False)
        session.query(Module).delete(synchronize_session=False)
        session.query(Course).delete(synchronize_session=False)
        # session.query(User).delete(synchronize_session=False) # Typically users are not cleared on reseed unless intended
        session.commit()
        logger.info("Successfully cleared existing data.")
    except Exception as e:
        session.rollback()
        logger.error(f"Error clearing data: {e}", exc_info=True)
        raise

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


def seed_course_exams(session: SQLAlchemySession):
    logger.info("Seeding course exams (placeholder)...")
    # Implement if you have seed_course_exams.json and seed_exam_questions.json
    # Example:
    # with open(os.path.join(os.path.dirname(__file__), "seed_data/seed_course_exams.json"), encoding="utf-8") as f:
    #     exams_data = json.load(f)
    #     for exam_item_data in exams_data:
    #         if not session.query(CourseExam).filter_by(id=exam_item_data["id"]).first():
    #             # Pop questions if they are to be seeded separately or handled by relationships
    #             questions_list = exam_item_data.pop("questions", [])
    #             exam = CourseExam(**exam_item_data)
    #             session.add(exam)
    #             # If questions are in the same file and need to be added:
    #             # for q_data in questions_list:
    #             #    session.add(ExamQuestion(exam=exam, **q_data))
    #     session.commit()
    logger.info("Course exams seeding process complete.")

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
        "course_exams_id_seq",
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

if __name__ == "__main__":
    logger.info("Starting database seeding process...")
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        # --- Migration detection logic ---
        current_migration_hash = get_current_migration_hash()
        last_seeded_hash = get_last_seeded_migration_hash()
        progress_tables_need_reset = current_migration_hash != last_seeded_hash

        if progress_tables_need_reset:
            logger.warning("Migration affecting progress tables detected. Clearing progress data.")
            # Only clear progress tables, not content tables!
            session.query(UserExerciseSubmission).delete(synchronize_session=False)
            session.query(UserLessonProgress).delete(synchronize_session=False)
            session.query(UserModuleProgress).delete(synchronize_session=False)
            session.query(UserExamAttempt).delete(synchronize_session=False)
            session.query(UserCourseEnrollment).delete(synchronize_session=False)
            session.commit()
            # --- RESET SEQUENCES HERE ---
            reset_postgres_sequences(session)
            set_last_seeded_migration_hash(current_migration_hash)
        else:
            logger.info("No migration affecting progress tables detected. Progress data will be preserved.")

        # Always seed content tables (idempotent)
        logger.info("Seeding core content (courses, modules, lessons, exercises, users, exams)...")
        seed_courses(session)
        seed_modules(session)
        seed_lessons(session)
        seed_exercises(session)
        seed_course_exams(session)
        seed_users(session)
        logger.info("Core content seeding complete.")

    except Exception as e:
        logger.error(f"CRITICAL ERROR during seeding process: {e}", exc_info=True)
        session.rollback()
        logger.error("Seeding process failed and transaction was rolled back.")
    finally:
        session.close()
        logger.info("Database session closed.")
