from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
import os

# Create base for all models
Base = declarative_base()

# Import all models to register them with Base
from .content import Course, Module, Lesson
from .user import User, Progress

# Database connection (for standalone use)
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
