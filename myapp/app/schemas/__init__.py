"""Pydantic schemas. Rails equivalent: strong params + serializers."""

from app.schemas.user_schema import (
    UserCreateSchema,
    UserUpdateSchema,
    UserResponseSchema,
    UserListSchema,
    LoginSchema,
    TokenSchema,
    RefreshSchema,
)
from app.schemas.post_schema import (
    PostCreateSchema,
    PostUpdateSchema,
    PostResponseSchema,
    PostListSchema,
    PaginationMeta,
)

__all__ = [
    "UserCreateSchema",
    "UserUpdateSchema",
    "UserResponseSchema",
    "UserListSchema",
    "LoginSchema",
    "TokenSchema",
    "RefreshSchema",
    "PostCreateSchema",
    "PostUpdateSchema",
    "PostResponseSchema",
    "PostListSchema",
    "PaginationMeta",
]
