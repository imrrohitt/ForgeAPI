"""
User business logic. Rails equivalent: UsersController + User model callbacks offloaded.
"""

from typing import Any

from fastapi import HTTPException
from sqlalchemy import select, func

from app.models.user import User
from app.schemas.user_schema import UserCreateSchema, UserUpdateSchema
from app.services.base_service import BaseService
from config.settings import get_settings

settings = get_settings()


class UserService(BaseService):
    """User CRUD and auth."""

    def list_users(
        self,
        page: int = 1,
        per_page: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Paginated list of users."""
        per_page = per_page or settings.DEFAULT_PAGE_SIZE
        per_page = min(per_page, settings.MAX_PAGE_SIZE)
        filters = filters or {}
        stmt = select(User)
        for key, value in filters.items():
            if hasattr(User, key) and value is not None:
                stmt = stmt.where(getattr(User, key) == value)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0
        offset = (page - 1) * per_page
        items = list(self.db.execute(stmt.offset(offset).limit(per_page)).scalars().all())
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

    def get_user(self, user_id: int) -> dict[str, Any]:
        """Get one user by id."""
        user = User.find_by(self.db, id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return self.success(user)

    def create_user(self, payload: UserCreateSchema) -> dict[str, Any]:
        """Create user from schema (password hashed in model callback)."""
        if User.find_by(self.db, email=payload.email.lower()):
            raise HTTPException(status_code=422, detail="Email already registered")
        user = User(
            email=payload.email,
            name=payload.name,
            hashed_password=payload.password,
            role=payload.role or "user",
        )
        user.save(self.db)
        return self.success(user)

    def update_user(self, user: User, payload: UserUpdateSchema) -> dict[str, Any]:
        """Update user with partial data."""
        data = payload.model_dump(exclude_unset=True)
        if "email" in data and data["email"]:
            existing = User.find_by(self.db, email=data["email"].lower())
            if existing and existing.id != user.id:
                raise HTTPException(status_code=422, detail="Email already taken")
        user.update(self.db, **data)
        return self.success(user)

    def delete_user(self, user: User) -> dict[str, Any]:
        """Permanently delete user."""
        user.destroy(self.db)
        return self.success({"deleted": True})

    def change_password(self, user: User, old_password: str, new_password: str) -> dict[str, Any]:
        """Change password after verifying old one."""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not pwd_context.verify(old_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid current password")
        if len(new_password) < 8:
            raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
        user.hashed_password = new_password
        user.save(self.db)
        return self.success({"updated": True})

    def authenticate(self, email: str, password: str) -> User:
        """Verify credentials and return user or raise."""
        user = User.find_by(self.db, email=email.lower())
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account disabled")
        return user
