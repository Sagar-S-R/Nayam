"""
NAYAM (नयम्) — Citizen Pydantic Schemas.

Request/response models for citizen CRUD operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CitizenCreateRequest(BaseModel):
    """Schema for creating a new citizen."""
    name: str = Field(..., min_length=2, max_length=255, description="Full name")
    contact_number: str = Field(..., min_length=5, max_length=20, description="Phone number")
    ward: str = Field(..., min_length=1, max_length=100, description="Administrative ward")


class CitizenUpdateRequest(BaseModel):
    """Schema for updating an existing citizen. All fields optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    contact_number: Optional[str] = Field(None, min_length=5, max_length=20)
    ward: Optional[str] = Field(None, min_length=1, max_length=100)


class CitizenResponse(BaseModel):
    """Schema for citizen data in responses."""
    id: UUID
    name: str
    contact_number: str
    ward: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CitizenListResponse(BaseModel):
    """Schema for paginated citizen list."""
    total: int
    citizens: list[CitizenResponse]
