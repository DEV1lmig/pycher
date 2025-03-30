from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models import User, Progress
from schemas import UserCreate, ProgressCreate
from utils import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from typing import List

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def get_user_progress(db: Session, user_id: int):
    return db.query(Progress).filter(Progress.user_id == user_id).all()

def update_lesson_progress(db: Session, user_id: int, progress: ProgressCreate):
    # Check if progress record already exists
    db_progress = db.query(Progress).filter(
        Progress.user_id == user_id,
        Progress.module_id == progress.module_id,
        Progress.lesson_id == progress.lesson_id
    ).first()

    if db_progress:
        # Update existing record
        db_progress.completed = progress.completed
        if progress.completed:
            db_progress.completion_date = db.func.now()
    else:
        # Create new progress record
        db_progress = Progress(
            user_id=user_id,
            module_id=progress.module_id,
            lesson_id=progress.lesson_id,
            completed=progress.completed
        )
        if progress.completed:
            db_progress.completion_date = db.func.now()
        db.add(db_progress)

    db.commit()
    db.refresh(db_progress)
    return db_progress
