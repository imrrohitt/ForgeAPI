"""
Authenticatable concern: authenticate_user, require_admin, require_owner.
Rails equivalent: before_action :authenticate_user! + current_user
"""

from typing import Any

from fastapi import HTTPException
from starlette.requests import Request


class Authenticatable:
    """Mixin for controllers that need current_user, require_admin, require_owner."""

    def authenticate_user(self) -> None:
        """Set self.current_user from request.state or raise 401."""
        user = getattr(self.request.state, "current_user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")
        self.current_user = user

    def require_admin(self) -> None:
        """Raise 403 if current_user is not admin."""
        if not getattr(self, "current_user", None):
            self.authenticate_user()
        if not self.current_user.is_admin():
            raise HTTPException(status_code=403, detail="Admin required")

    def require_owner(self, resource: Any) -> None:
        """Raise 403 if current_user does not own the resource (resource.user_id == current_user.id)."""
        if not getattr(self, "current_user", None):
            self.authenticate_user()
        owner_id = getattr(resource, "user_id", None)
        if owner_id is None:
            owner_id = getattr(resource, "id", None)
        if owner_id != self.current_user.id and not self.current_user.is_admin():
            raise HTTPException(status_code=403, detail="Not authorized to access this resource")
