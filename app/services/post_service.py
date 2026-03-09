"""
Post business logic. Rails equivalent: PostsController + Post model.
"""

from typing import Any

from sqlalchemy import select, func

from app.models.post import Post
from app.models.user import User
from app.schemas.post_schema import PostCreateSchema, PostUpdateSchema
from app.services.base_service import BaseService


class PostService(BaseService):
    """Post CRUD, publish/unpublish, soft delete."""

    def list_posts(
        self,
        page: int = 1,
        per_page: int = 20,
        published_only: bool = False,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        """Paginated list; optional filter by published and/or user_id."""
        from config.settings import get_settings
        settings = get_settings()
        per_page = min(per_page, settings.MAX_PAGE_SIZE)
        stmt = select(Post).where(Post.deleted_at.is_(None))
        if published_only:
            stmt = stmt.where(Post.published.is_(True))
        if user_id is not None:
            stmt = stmt.where(Post.user_id == user_id)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0
        offset = (page - 1) * per_page
        stmt = stmt.order_by(Post.created_at.desc()).offset(offset).limit(per_page)
        items = list(self.db.execute(stmt).scalars().all())
        total_pages = (total + per_page - 1) // per_page if total else 0
        return self.success({
            "data": items,
            "meta": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        })

    def get_post(self, post_id: int) -> dict[str, Any]:
        """Get one post by id (exclude soft-deleted unless explicitly requested)."""
        post = Post.find_by(self.db, id=post_id)
        if not post:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Post not found")
        if post.deleted_at:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Post not found")
        return self.success(post)

    def create_post(self, user: User, payload: PostCreateSchema) -> dict[str, Any]:
        """Create post for user."""
        post = Post(
            title=payload.title,
            body=payload.body,
            published=payload.published,
            user_id=user.id,
        )
        post.save(self.db)
        return self.success(post)

    def update_post(self, post: Post, payload: PostUpdateSchema) -> dict[str, Any]:
        """Update post with partial data."""
        data = payload.model_dump(exclude_unset=True)
        post.update(self.db, **data)
        return self.success(post)

    def publish_post(self, post: Post) -> dict[str, Any]:
        """Set published=True (published_at set in model callback)."""
        post.published = True
        post.save(self.db)
        return self.success(post)

    def unpublish_post(self, post: Post) -> dict[str, Any]:
        """Set published=False."""
        post.published = False
        post.save(self.db)
        return self.success(post)

    def delete_post(self, post: Post) -> dict[str, Any]:
        """Soft delete post."""
        post.soft_delete(self.db)
        return self.success({"deleted": True})
