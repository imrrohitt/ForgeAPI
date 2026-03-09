"""
User model with callbacks and scopes.
Rails equivalent: app/models/user.rb
"""

from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel, before_save, after_create, before_destroy
from app.models.concerns.timestampable import Timestampable

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models.post import Post


class User(BaseModel, Timestampable):
    """User model. Columns: id, email, name, hashed_password, is_active, role, created_at, updated_at."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="user", nullable=False)
    created_at: Mapped["__import__('datetime').datetime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped["__import__('datetime').datetime"] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    posts: Mapped[list["Post"]] = relationship("Post", back_populates="user", lazy="selectin")

    @before_save
    def _hash_password_if_changed(self, db: "Session") -> None:
        """Hash password only when it looks like plaintext (no bcrypt prefix)."""
        pw = getattr(self, "hashed_password", "") or ""
        if pw and not pw.startswith("$2b$") and not pw.startswith("$2a$"):
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            self.hashed_password = pwd_context.hash(pw)

    @before_save
    def _downcase_email(self, db: "Session") -> None:
        """Normalize email to lowercase."""
        if self.email:
            self.email = self.email.lower().strip()

    @after_create
    def _enqueue_welcome_email(self, db: "Session") -> None:
        """Enqueue WelcomeEmailJob after user creation."""
        from app.jobs.welcome_email_job import WelcomeEmailJob
        WelcomeEmailJob.perform_later(user_id=self.id)

    @before_destroy
    def _soft_delete_posts(self, db: "Session") -> None:
        """Soft-delete all posts when user is destroyed."""
        from app.models.post import Post
        for post in db.execute(select(Post).where(Post.user_id == self.id)).scalars().all():
            if hasattr(post, "soft_delete"):
                post.soft_delete(db)

    def is_admin(self) -> bool:
        """True if role is admin."""
        return self.role == "admin"

    def has_role(self, role: str) -> bool:
        """True if user has the given role."""
        return self.role == role

    @classmethod
    def active(cls, db: "Session") -> list["User"]:
        """Scope: is_active=True."""
        return cls.where(db, is_active=True)
