import json
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shared.models import Base, Course, Module, Lesson, User, Progress

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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

def seed_users():
    # Similar implementation for users
    pass

if __name__ == "__main__":
    seed_courses()
    seed_modules()
    seed_lessons()
    seed_users()
