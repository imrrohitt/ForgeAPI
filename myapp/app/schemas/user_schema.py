"""
Pydantic schemas for User and Auth.
Rails equivalent: strong_parameters + jbuilder/serializer
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreateSchema(BaseModel):
    """Schema for creating a user."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[str] = Field(default="user", pattern="^(user|admin|moderator)$")

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserUpdateSchema(BaseModel):
    """Schema for updating a user (all fields optional)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None


class UserResponseSchema(BaseModel):
    """Schema for user in API responses (no password)."""

    id: int
    email: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""

    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class UserListSchema(BaseModel):
    """Paginated list of users."""

    data: list[UserResponseSchema]
    meta: PaginationMeta


class LoginSchema(BaseModel):
    """Credentials for login."""

    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    """JWT token pair response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshSchema(BaseModel):
    """Refresh token request body."""

    refresh_token: str
