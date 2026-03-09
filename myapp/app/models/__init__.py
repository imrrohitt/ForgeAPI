"""Models package. Exports User, Post, BaseModel."""

from app.models.user import User
from app.models.post import Post
from app.models.base_model import BaseModel

__all__ = ["User", "Post", "BaseModel"]
