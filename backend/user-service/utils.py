from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import os
import redis

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Redis client for session management
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_user = os.getenv("REDIS_USER")          # e.g. "pycher"
redis_password = os.getenv("REDIS_PASSWORD")  # e.g. "3810"

redis_client = redis.Redis(
    host=redis_host,
    port=redis_port,
    username=redis_user,
    password=redis_password,
    decode_responses=True
)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt

def check_login_attempts(username: str):
    """Check if a user has exceeded login attempts"""
    key = f"login_attempts:{username}"
    attempts = redis_client.get(key)

    if attempts is None:
        # First attempt
        redis_client.setex(key, 3600, 1)  # 1 hour window
        return True

    attempts = int(attempts)  # <-- FIXED: removed .decode()
    if attempts >= 5:  # Maximum 5 attempts per hour
        return False

    # Increment attempts
    redis_client.incr(key)
    return True
