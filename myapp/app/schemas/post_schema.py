"""
Pydantic schemas for Post.
Rails equivalent: strong_parameters + serializers
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.user_schema import PaginationMeta


class PostCreateSchema(BaseModel):
    """Schema for creating a post."""

    title: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    published: bool = False


class PostUpdateSchema(BaseModel):
    """Schema for updating a post (all optional)."""

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    body: Optional[str] = None
    published: Optional[bool] = None


class PostResponseSchema(BaseModel):
    """Schema for post in API responses."""

    id: int
    title: str
    slug: Optional[str] = None
    body: str
    published: bool
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PostListSchema(BaseModel):
    """Paginated list of posts."""

    data: list[PostResponseSchema]
    meta: PaginationMeta
