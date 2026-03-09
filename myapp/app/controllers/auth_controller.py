"""
Auth controller: login, register, logout, me, refresh.
Rails equivalent: app/controllers/sessions_controller + registrations
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.base_controller import BaseController
from app.controllers.concerns.authenticatable import Authenticatable
from app.helpers.jwt_helper import JWTHelper
from app.schemas.user_schema import (
    LoginSchema,
    UserCreateSchema,
    UserResponseSchema,
    TokenSchema,
    RefreshSchema,
)
from app.services.user_service import UserService


class AuthController(BaseController, Authenticatable):
    """No before_action on most routes. /auth/me and /auth/refresh require auth."""

    async def login(self) -> JSONResponse:
        """POST /auth/login - returns JWT tokens."""
        body = await self.request.json()
        payload = LoginSchema.model_validate(body)
        svc = UserService(self.db)
        user = svc.authenticate(payload.email, payload.password)
        access = JWTHelper.create_access_token(user.id, user.email, user.role)
        refresh = JWTHelper.create_refresh_token(user.id)
        return self.render_json(
            TokenSchema(access_token=access, refresh_token=refresh).model_dump()
        )

    async def register(self) -> JSONResponse:
        """POST /auth/register - create user and return tokens."""
        body = await self.request.json()
        payload = UserCreateSchema.model_validate(body)
        svc = UserService(self.db)
        result = svc.create_user(payload)
        user = result["data"]
        access = JWTHelper.create_access_token(user.id, user.email, user.role)
        refresh = JWTHelper.create_refresh_token(user.id)
        return self.render_json(
            TokenSchema(access_token=access, refresh_token=refresh).model_dump(),
            status=201,
        )

    def logout(self) -> JSONResponse:
        """POST /auth/logout - client should discard tokens."""
        return self.render_json({"message": "Logged out"})

    def me(self) -> JSONResponse:
        """GET /auth/me - current user (requires auth)."""
        self.authenticate_user()
        return self.render_json(
            UserResponseSchema.model_validate(self.current_user).model_dump(mode="json")
        )

    async def refresh(self) -> JSONResponse:
        """POST /auth/refresh - new access token from refresh token."""
        body = await self.request.json()
        payload = RefreshSchema.model_validate(body)
        try:
            decoded = JWTHelper.decode_token(payload.refresh_token)
            if decoded.get("type") != "refresh":
                return self.render_error("Invalid refresh token", 401)
            from app.models.user import User
            user_id = int(decoded["sub"])
            user = self.db.get(User, user_id)
            if not user or not user.is_active:
                return self.render_error("User not found", 401)
            access = JWTHelper.create_access_token(user.id, user.email, user.role)
            return self.render_json(
                TokenSchema(access_token=access, refresh_token=payload.refresh_token).model_dump()
            )
        except Exception:
            return self.render_error("Invalid refresh token", 401)
