"""
Pydantic schemas for authentication and user management.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from app.models.user import UserRole


class UserCreate(BaseModel):
    """
    Schema for user registration.
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password (minimum 8 characters)")


class UserLogin(BaseModel):
    """
    Schema for user login.
    """
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserResponse(BaseModel):
    """
    Schema for user data in responses (without sensitive information).
    """
    id: UUID
    email: EmailStr
    is_active: bool
    role: UserRole
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class Token(BaseModel):
    """
    Schema for authentication token response.
    """
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    user: UserResponse = Field(..., description="User data")


class TokenData(BaseModel):
    """
    Schema for data encoded in JWT token.
    """
    user_id: UUID | None = None
    email: str | None = None
    token_type: str = "access"  # "access" or "refresh"


class RefreshTokenRequest(BaseModel):
    """
    Schema for refresh token request.
    """
    refresh_token: str = Field(..., description="JWT refresh token")
