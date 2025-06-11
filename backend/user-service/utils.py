from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import redis
from typing import Optional
import random
import string

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )
    # Test connection
    redis_client.ping()
    print(f"✅ Redis connected successfully at {REDIS_HOST}:{REDIS_PORT}")
except redis.ConnectionError as e:
    print(f"❌ Redis connection failed: {e}")
    print("⚠️  Falling back to memory-based session storage")
    # Create a mock redis client for development
    class MockRedis:
        def __init__(self):
            self._store = {}

        def setex(self, key, seconds, value):
            self._store[key] = value
            return True

        def get(self, key):
            return self._store.get(key)

        def delete(self, key):
            if key in self._store:
                del self._store[key]
                return 1
            return 0

        def ping(self):
            return True

    redis_client = MockRedis()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_input_from_constraints(constraints: dict) -> str:
    input_type = constraints.get("type", "string")
    if input_type == "string":
        min_len = constraints.get("min_length", 1)
        max_len = constraints.get("max_length", 10)
        length = random.randint(min_len, max_len)
        charset_type = constraints.get("charset", "alphanumeric")
        char_pool = ""
        if charset_type == "alpha":
            char_pool = string.ascii_letters
        elif charset_type == "alphanumeric":
            char_pool = string.ascii_letters + string.digits
        elif charset_type == "numeric":
            char_pool = string.digits
        else: # Default to alphanumeric if unknown
            char_pool = string.ascii_letters + string.digits

        if not char_pool: # Should not happen with defaults
            return "test"
        return ''.join(random.choice(char_pool) for _ in range(length))
    # Extend for other types like "integer" if needed
    logger.warning(f"Unsupported input generation type: {input_type}. Returning default.")
    return "default_gen_input"
