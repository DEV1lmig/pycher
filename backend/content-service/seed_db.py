import json
import os
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Course, Module, Lesson

def seed_courses():
    session = SessionLocal()
    with open(os.path.join(os.path.dirname(__file__), "seed_courses.json"), encoding="utf-8") as f:
        courses = json.load(f)
        for course in courses:
            if not session.query(Course).filter_by(id=course["id"]).first():
                session.add(Course(**course))
        session.commit()
    session.close()

def seed_modules():
    session = SessionLocal()
    with open(os.path.join(os.path.dirname(__file__), "seed_modules.json"), encoding="utf-8") as f:
        modules = json.load(f)
        for module in modules:
            if not session.query(Module).filter_by(id=module["id"]).first():
                session.add(Module(**module))
        session.commit()
    session.close()

def seed_lessons():
    session = SessionLocal()
    with open(os.path.join(os.path.dirname(__file__), "seed_lessons.json"), encoding="utf-8") as f:
        lessons = json.load(f)
        for lesson in lessons:
            if not session.query(Lesson).filter_by(id=lesson["id"]).first():
                session.add(Lesson(**lesson))
        session.commit()
    session.close()

if __name__ == "__main__":
    seed_courses()
    seed_modules()
    seed_lessons()
