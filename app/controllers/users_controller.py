"""
Users controller: index, show, create, update, destroy.
Rails equivalent: app/controllers/users_controller.rb
"""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.base_controller import BaseController, before_action
from app.controllers.concerns.authenticatable import Authenticatable
from app.models.user import User
from app.schemas.user_schema import UserCreateSchema, UserUpdateSchema, UserResponseSchema
from app.services.user_service import UserService


class UsersController(BaseController, Authenticatable):
    """
    before_action: authenticate_user (all)
    before_action: set_user, only show, update, destroy
    before_action: require_admin, only destroy
    """

    def _set_user(self) -> None:
        """Load user from path id. Run before show, update, destroy."""
        uid = int(self.request.path_params["id"])
        self._user = User.find(self.db, uid)

    @before_action(only=["show", "update", "destroy"])
    def set_user(self) -> None:
        self._set_user()

    @before_action
    def authenticate_user_filter(self) -> None:
        self.authenticate_user()

    @before_action(only=["destroy"])
    def require_admin_filter(self) -> None:
        self.require_admin()

    def index(self) -> JSONResponse:
        """GET /users - paginated list."""
        self.authenticate_user()
        page = int(self.request.query_params.get("page", 1))
        per_page = int(self.request.query_params.get("per_page", 20))
        svc = UserService(self.db)
        result = svc.list_users(page=page, per_page=per_page)
        data = result["data"]
        items = [UserResponseSchema.model_validate(u) for u in data["data"]]
        return self.render_json([m.model_dump(mode="json") for m in items], meta=data["meta"])

    def show(self) -> JSONResponse:
        """GET /users/:id."""
        user = getattr(self, "_user", None) or User.find(self.db, int(self.request.path_params["id"]))
        return self.render_json(UserResponseSchema.model_validate(user).model_dump(mode="json"))

    async def create(self) -> JSONResponse:
        """POST /users."""
        self.authenticate_user()
        body = await self.request.json()
        payload = UserCreateSchema.model_validate(body)
        svc = UserService(self.db)
        result = svc.create_user(payload)
        user = result["data"]
        return self.render_json(UserResponseSchema.model_validate(user).model_dump(mode="json"), status=201)

    async def update(self) -> JSONResponse:
        """PUT /users/:id."""
        user = getattr(self, "_user", None) or User.find(self.db, int(self.request.path_params["id"]))
        body = await self.request.json()
        payload = UserUpdateSchema.model_validate(body)
        svc = UserService(self.db)
        result = svc.update_user(user, payload)
        return self.render_json(UserResponseSchema.model_validate(result["data"]).model_dump(mode="json"))

    def destroy(self) -> JSONResponse:
        """DELETE /users/:id."""
        user = getattr(self, "_user", None) or User.find(self.db, int(self.request.path_params["id"]))
        svc = UserService(self.db)
        svc.delete_user(user)
        return self.render_json({"deleted": True})
