import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from database import get_db
from jose import jwt, JWTError
from models import engine, Progress
from schemas import UserCreate, UserResponse, Token, ProgressCreate, ProgressResponse, ModuleProgress
from services import create_user, get_user_by_username, get_user_by_email, authenticate_user, get_user_progress, update_lesson_progress
from utils import create_access_token, redis_client, get_password_hash, SECRET_KEY, ALGORITHM
from auth import get_current_user
router = APIRouter()
# Configure logging at the top of your file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("user-service")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Log the registration attempt (omit password)
    logger.info(f"Registration attempt - Username: {user.username}, Email: {user.email}")

    db_user = get_user_by_username(db, user.username)
    if db_user:
        logger.warning(f"Registration failed - Username already exists: {user.username}")
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

    logger.info(f"User registered successfully - Username: {user.username}")
    return create_user(db, user)

# Modify the login endpoint to use rate limiting

@router.post("/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Log the login attempt (omit password)
    logger.info(f"Login attempt - Username: {form_data.username}")

    # Check rate limiting
    if not check_login_attempts(form_data.username):
        logger.warning(f"Login blocked: Too many attempts - Username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later."
        )

    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Login failed: Invalid credentials - Username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Log successful login
    logger.info(f"Login successful - Username: {form_data.username}, User ID: {user.id}")

    # Reset login attempts on successful login
    redis_client.delete(f"login_attempts:{form_data.username}")
    logger.info(f"Reset login attempts for user: {form_data.username}")

    access_token_expires = timedelta(minutes=30)
    refresh_token_expires = timedelta(days=7)

    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username}, expires_delta=refresh_token_expires
    )

    # Log token storage
    logger.info(f"Generated tokens for user: {form_data.username}")

    # Store tokens in Redis
    redis_client.setex(
        f"token:{user.username}",
        int(access_token_expires.total_seconds()),
        access_token
    )
    redis_client.setex(
        f"refresh_token:{user.username}",
        int(refresh_token_expires.total_seconds()),
        refresh_token
    )
    logger.info(f"Stored tokens in Redis for user: {form_data.username}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout_user(current_user = Depends(get_current_user)):
    # Remove token from Redis
    redis_client.delete(f"token:{current_user.username}")
    return {"detail": "Successfully logged out"}

# Add this endpoint

@router.post("/refresh", response_model=Token)
def refresh_access_token(refresh_token: str, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Verify refresh token is in Redis
    stored_refresh_token = redis_client.get(f"refresh_token:{username}")
    if stored_refresh_token is None or stored_refresh_token.decode() != refresh_token:
        raise credentials_exception

    # Create new access token
    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exception

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )

    # Update access token in Redis
    redis_client.setex(
        f"token:{username}",
        int(access_token_expires.total_seconds()),
        access_token
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

# Modify the existing progress endpoints to use the current_user dependency

@router.post("/progress", response_model=dict)
def set_lesson_progress(
    progress: ProgressCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return update_lesson_progress(db, current_user.id, progress)

@router.get("/progress/{module_id}", response_model=List[dict])
def get_progress(
    module_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_progress(db, current_user.id, module_id)

# Add the following functions to utils.py:
def check_login_attempts(username: str):
    key = f"login_attempts:{username}"
    attempts = redis_client.get(key)
    if attempts is None:
        redis_client.setex(key, 3600, 1)
        return True
    attempts = int(attempts)
    if attempts >= 5:
        return False
    redis_client.incr(key)
    return True

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
