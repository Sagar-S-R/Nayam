"""
NAYAM (नयम्) — User / Authentication Pydantic Schemas.

Defines request/response models for registration, login, and user data.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


# ── Request Schemas ──────────────────────────────────────────────────
class UserRegisterRequest(BaseModel):
    """Schema for user registration requests."""
    name: str = Field(..., min_length=2, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Unique email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password (min 8 chars)")
    role: UserRole = Field(default=UserRole.STAFF, description="User role")


class UserLoginRequest(BaseModel):
    """Schema for user login requests."""
    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")


# ── Response Schemas ─────────────────────────────────────────────────
class UserResponse(BaseModel):
    """Schema for user data in responses."""
    id: UUID
    name: str
    email: str
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Schema for JWT token responses."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None
