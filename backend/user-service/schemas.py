from pydantic import BaseModel, EmailStr, validator, Field
from typing import Optional, List
from datetime import datetime
import re

ALLOWED_DOMAINS = {"gmail.com", "outlook.com", "yahoo.com", "hotmail.com", "urbe.edu.ve"}

# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class UserCreate(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=32, pattern=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$")
    last_name: str = Field(..., min_length=2, max_length=32, pattern=r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s'-]+$")
    username: str = Field(..., min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: EmailStr
    password: str
    accept_terms: bool

    @validator("email")
    def email_domain_allowed(cls, v):
        domain = v.split("@")[1].lower()
        if domain not in ALLOWED_DOMAINS:
            raise ValueError("Dominio de correo no permitido")
        return v

    @validator("password")
    def password_strength(cls, v):
        if (len(v) < 8 or len(v) > 64 or
            not re.search(r"[A-Z]", v) or
            not re.search(r"[a-z]", v) or
            not re.search(r"\d", v) or
            not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", v)):
            raise ValueError("La contraseña debe tener entre 8 y 64 caracteres, mayúsculas, minúsculas, número y símbolo")
        return v

    @validator("accept_terms")
    def terms_must_be_accepted(cls, v):
        if not v:
            raise ValueError("Debes aceptar los términos")
        return v

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ProgressBase(BaseModel):
    module_id: str
    lesson_id: str
    completed: bool = False

class ProgressCreate(ProgressBase):
    pass

class ProgressResponse(ProgressBase):
    id: int
    user_id: int
    completion_date: Optional[datetime] = None

    class Config:
        from_attributes = True

class ModuleProgress(BaseModel):
    module_id: str
    completed_lessons: int
    total_lessons: int
    percentage: float

# Add these schemas

class PasswordResetRequest(BaseModel):
    email: str

class PasswordReset(BaseModel):
    token: str
    new_password: str

class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_.@-]+$")
    password: str = Field(..., min_length=8, max_length=64)
