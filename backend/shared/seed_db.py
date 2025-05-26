import json
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Ensure all models that need to be cleared are imported
from models import (
    Base, Course, Module, Lesson, User, Progress, Exercise,
    UserCourseEnrollment, UserModuleProgress, UserLessonProgress,
    UserExerciseSubmission, CourseExam, UserExamAttempt
)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def clear_data():
    """Deletes all data from relevant tables to allow fresh seeding."""
    session = SessionLocal()
    try:
        # Delete in an order that respects foreign key constraints
        # Start with tables that are most dependent or act as join tables for progress

        session.query(UserExerciseSubmission).delete(synchronize_session=False)
        session.query(Progress).delete(synchronize_session=False) # This is the old 'user_progress' table
        session.query(UserLessonProgress).delete(synchronize_session=False)
        session.query(UserModuleProgress).delete(synchronize_session=False)
        session.query(UserExamAttempt).delete(synchronize_session=False)

        # Now delete UserCourseEnrollment which links Users to Courses and their overall progress
        session.query(UserCourseEnrollment).delete(synchronize_session=False)

        # Then content items that might be referenced by the above, or by each other
        session.query(Exercise).delete(synchronize_session=False)
        session.query(Lesson).delete(synchronize_session=False)
        session.query(CourseExam).delete(synchronize_session=False) # Exams linked to courses
        session.query(Module).delete(synchronize_session=False)

        # Finally, the main Course table
        session.query(Course).delete(synchronize_session=False)

        # Optionally, clear users if they should also be reset during seeding
        # session.query(User).delete(synchronize_session=False)

        session.commit()
        print("Successfully cleared existing data.")
    except Exception as e:
        session.rollback()
        print(f"Error clearing data: {e}") # This will print the foreign key violation if order is still wrong
    finally:
        session.close()

def seed_courses():
    session = SessionLocal()
    with open(os.path.join(os.path.dirname(__file__), "seed_data/seed_courses.json"), encoding="utf-8") as f:
        courses = json.load(f)
        for course_data in courses:
            # Remove "total_modules" from the data if present, as it is computed dynamically.
            course_data.pop("total_modules", None)
            if not session.query(Course).filter_by(id=course_data["id"]).first():
                session.add(Course(**course_data))
        session.commit()
    session.close()

def seed_modules():
    session = SessionLocal()
    with open(os.path.join(os.path.dirname(__file__), "seed_data/seed_modules.json"), encoding="utf-8") as f:
        modules = json.load(f)
        for module_data in modules:
            if not session.query(Module).filter_by(id=module_data["id"]).first():
                session.add(Module(**module_data))
        session.commit()
    session.close()

def seed_lessons():
    session = SessionLocal()
    with open(os.path.join(os.path.dirname(__file__), "seed_data/seed_lessons.json"), encoding="utf-8") as f:
        lessons = json.load(f)
        for lesson_data in lessons:
            if not session.query(Lesson).filter_by(id=lesson_data["id"]).first():
                session.add(Lesson(**lesson_data))
        session.commit()
    session.close()

def seed_exercises():
    session = SessionLocal()
    with open(os.path.join(os.path.dirname(__file__), "seed_data/seed_exercises.json"), encoding="utf-8") as f:
        exercises = json.load(f)
        for exercise_data in exercises:
            # Remove id if not present (optional, for autoincrement)
            exercise_id = exercise_data.get("id")
            if exercise_id is not None:
                exists = session.query(Exercise).filter_by(id=exercise_id).first()
            else:
                exists = None

            # Ensure module_id and lesson_id are valid if provided
            # This is a basic check; more robust validation might be needed
            # depending on your data integrity requirements.
            if "module_id" in exercise_data and exercise_data["module_id"] is not None:
                if not session.query(Module).filter_by(id=exercise_data["module_id"]).first():
                    print(f"Warning: Module with id {exercise_data['module_id']} not found for exercise {exercise_data.get('title', exercise_id)}. Skipping.")
                    continue # Skip this exercise if its module doesn't exist

            if "lesson_id" in exercise_data and exercise_data["lesson_id"] is not None:
                if not session.query(Lesson).filter_by(id=exercise_data["lesson_id"]).first():
                    print(f"Warning: Lesson with id {exercise_data['lesson_id']} not found for exercise {exercise_data.get('title', exercise_id)}. Skipping.")
                    continue # Skip this exercise if its lesson doesn't exist

            if not exists:
                session.add(Exercise(**exercise_data))
        session.commit()
    session.close()

def seed_users():
    # Similar implementation for users
    pass

def seed_course_exams(): # Assuming you have a function to seed exams
    # ... implementation ...
    pass

def seed_progress_data(): # Placeholder if you seed detailed progress directly
    # ... implementation ...
    pass

if __name__ == "__main__":
    print("Starting database seeding process...")
    Base.metadata.create_all(bind=engine) # Ensure tables are created

    clear_data()  # Clear existing data first

    print("Seeding courses...")
    seed_courses()
    print("Seeding modules...")
    seed_modules()
    print("Seeding lessons...")
    seed_lessons()
    print("Seeding exercises...")
    seed_exercises()
    print("Seeding course exams...") # If you have exams
    seed_course_exams()
    print("Seeding users...")
    seed_users()
    # print("Seeding progress data...") # If you seed progress directly
    # seed_progress_data()
    print("Database seeding completed.")
