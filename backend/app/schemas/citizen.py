"""
NAYAM (नयम्) — Citizen Pydantic Schemas.

Request/response models for citizen CRUD operations with validation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, computed_field

from app.core.mcd_wards import get_valid_wards
from app.core.phone_utils import validate_indian_phone, mask_phone_number
from app.core.security_utils import sanitize_text


class CitizenCreateRequest(BaseModel):
    """Schema for creating a new citizen with validation."""
    name: str = Field(..., min_length=2, max_length=255, description="Full name")
    contact_number: str = Field(..., min_length=10, max_length=20, description="Indian phone number")
    ward: str = Field(..., description="MCD administrative ward")
    
    @field_validator("name", mode="before")
    @classmethod
    def sanitize_inputs(cls, v):
        return sanitize_text(v) if isinstance(v, str) else v
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name is not just symbols."""
        if not any(c.isalpha() for c in v):
            raise ValueError("Name must contain at least one letter")
        return v.strip()
    
    @field_validator("contact_number")
    @classmethod
    def validate_contact(cls, v: str) -> str:
        """Validate Indian phone number format."""
        is_valid, normalized = validate_indian_phone(v)
        if not is_valid:
            raise ValueError(
                "Invalid phone number. Must be Indian format: "
                "+91XXXXXXXXXX, 91XXXXXXXXXX, 0XXXXXXXXXX, or XXXXXXXXXX"
            )
        return normalized
    
    @field_validator("ward")
    @classmethod
    def validate_ward(cls, v: str) -> str:
        """Validate ward is one of valid MCD wards."""
        valid_wards = get_valid_wards()
        if v not in valid_wards:
            raise ValueError(
                f"Invalid ward. Must be one of: {', '.join(valid_wards)}"
            )
        return v


class CitizenUpdateRequest(BaseModel):
    """Schema for updating an existing citizen. All fields optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    contact_number: Optional[str] = Field(None, min_length=10, max_length=20)
    ward: Optional[str] = Field(None)
    
    @field_validator("name", mode="before")
    @classmethod
    def sanitize_inputs(cls, v):
        return sanitize_text(v) if isinstance(v, str) else v
    
    @field_validator("contact_number")
    @classmethod
    def validate_contact(cls, v: Optional[str]) -> Optional[str]:
        """Validate Indian phone number format if provided."""
        if v is None:
            return v
        is_valid, normalized = validate_indian_phone(v)
        if not is_valid:
            raise ValueError(
                "Invalid phone number. Must be Indian format: "
                "+91XXXXXXXXXX, 91XXXXXXXXXX, 0XXXXXXXXXX, or XXXXXXXXXX"
            )
        return normalized
    
    @field_validator("ward")
    @classmethod
    def validate_ward(cls, v: Optional[str]) -> Optional[str]:
        """Validate ward if provided."""
        if v is None:
            return v
        valid_wards = get_valid_wards()
        if v not in valid_wards:
            raise ValueError(
                f"Invalid ward. Must be one of: {', '.join(valid_wards)}"
            )
        return v


class CitizenResponse(BaseModel):
    """Schema for citizen data in responses with PII masking."""
    id: UUID
    name: str
    contact_number: str
    ward: str
    created_at: datetime
    
    @computed_field
    @property
    def masked_contact(self) -> str:
        """Compute masked contact number on-the-fly."""
        return mask_phone_number(self.contact_number, format_type="partial")
    
    @property
    def __str__(self):
        return f"Citizen(id={self.id}, name={self.name}, ward={self.ward})"

    model_config = {"from_attributes": True}


class CitizenListResponse(BaseModel):
    """Schema for paginated citizen list."""
    total: int
    citizens: list[CitizenResponse]
