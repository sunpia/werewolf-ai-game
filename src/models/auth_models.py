"""Authentication models for the Werewolf game backend."""

from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class User(BaseModel):
    """User model."""
    id: str
    email: EmailStr
    name: str
    picture: Optional[str] = None
    provider: str = "google"  # google, github, etc.
    created_at: datetime
    last_login: datetime


class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    name: str
    picture: Optional[str] = None
    provider: str = "google"


class UserResponse(BaseModel):
    """User response model."""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    provider: str


class Token(BaseModel):
    """Token model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None
    email: Optional[str] = None


class GoogleOAuthRequest(BaseModel):
    """Google OAuth request model."""
    credential: str  # Google ID token


class AuthResponse(BaseModel):
    """Authentication response model."""
    success: bool
    message: str
    user: Optional[UserResponse] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"
