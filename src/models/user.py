"""User-related Pydantic models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    """User roles."""

    USER = "user"
    ADMIN = "admin"
    PREMIUM = "premium"


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr
    full_name: str | None = None


class UserCreate(UserBase):
    """User registration request."""

    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update request."""

    full_name: str | None = None
    password: str | None = Field(default=None, min_length=8, max_length=100)


class UserResponse(UserBase):
    """User response model."""

    id: str
    is_active: bool = True
    role: UserRole = UserRole.USER
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int = Field(description="Token expiration time in seconds")


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # User ID
    email: str
    role: UserRole
    exp: datetime
    iat: datetime


class PasswordReset(BaseModel):
    """Password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=100)


class ChangePassword(BaseModel):
    """Change password request."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
