from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta
import json

from models import engine, Progress
from schemas import UserCreate, UserResponse, Token, ProgressCreate, ProgressResponse, ModuleProgress
from services import create_user, get_user_by_username, get_user_by_email, authenticate_user, get_user_progress, update_lesson_progress
from utils import create_access_token, redis_client

from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    db_email = get_user_by_email(db, user.email)
    if db_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return create_user(db, user)

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    # Store token in Redis for faster validation
    redis_client.setex(
        f"token:{user.username}",
        int(access_token_expires.total_seconds()),
        access_token
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/progress", response_model=ProgressResponse)
def set_lesson_progress(progress: ProgressCreate, user_id: int, db: Session = Depends(get_db)):
    return update_lesson_progress(db, user_id, progress)

@router.get("/progress/{user_id}/{module_id}", response_model=ModuleProgress)
def get_module_progress(user_id: int, module_id: str, db: Session = Depends(get_db)):
    # Get progress from content service to calculate percentage
    # For demo, we'll mock this with hardcoded values based on module_id
    if module_id == "beginner":
        total_lessons = 10
    elif module_id == "intermediate":
        total_lessons = 8
    else:  # advanced
        total_lessons = 6

    # Get user's completed lessons for this module
    user_progress = db.query(Progress).filter(
        Progress.user_id == user_id,
        Progress.module_id == module_id,
        Progress.completed == True
    ).all()

    completed_lessons = len(user_progress)
    percentage = (completed_lessons / total_lessons) * 100 if total_lessons > 0 else 0

    return {
        "module_id": module_id,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "percentage": percentage
    }
