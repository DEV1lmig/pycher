from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from utils import SECRET_KEY, ALGORITHM, redis_client
from services import get_user_by_username
from database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/token")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    # Verify token is in Redis (not revoked)
    stored_token = redis_client.get(f"token:{username}")
    if stored_token is None or stored_token != token:
        raise credentials_exc

    user = get_user_by_username(db, username)
    if user is None:
        raise credentials_exc
    return user
