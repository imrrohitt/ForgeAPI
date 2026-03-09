"""
Post model with slug, soft delete, and callbacks.
Rails equivalent: app/models/post.rb
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean, Text, ForeignKey, DateTime, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel, before_save
from app.models.concerns.timestampable import Timestampable
from app.models.concerns.soft_deletable import SoftDeletable
from app.models.concerns.sluggable import Sluggable

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from app.models.user import User


class Post(BaseModel, Timestampable, SoftDeletable, Sluggable):
    """
    Post model. Columns: id, title, slug, body, user_id, published, published_at, deleted_at, created_at, updated_at.
    """

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(500), unique=True, nullable=True, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="posts", lazy="selectin")

    @before_save
    def _generate_slug_from_title(self, db: "Session") -> None:
        """Auto-generate slug from title if slug is empty."""
        if not self.slug and self.title:
            self.generate_slug(from_field="title")
            self.ensure_unique_slug(db)

    @before_save
    def _set_published_at(self, db: "Session") -> None:
        """Set published_at when published changes to True."""
        if self.published and self.published_at is None:
            self.published_at = datetime.now(timezone.utc)

    @classmethod
    def published_scope(cls, db: "Session") -> list["Post"]:
        """Scope: published=True and not soft-deleted."""
        stmt = select(cls).where(cls.published.is_(True), cls.deleted_at.is_(None))
        return list(db.execute(stmt).scalars().all())

    @classmethod
    def draft_scope(cls, db: "Session") -> list["Post"]:
        """Scope: published=False."""
        return cls.where(db, published=False)
