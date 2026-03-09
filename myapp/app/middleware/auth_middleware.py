"""
Authentication middleware: validate JWT and set request.state.current_user.
Rails equivalent: before_action :authenticate_user!
"""

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.helpers.jwt_helper import JWTHelper
from app.models.user import User
from config.database import SessionLocal


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Reads Authorization: Bearer <token>, decodes JWT, loads user, sets request.state.current_user.
    Public routes (e.g. /health, /docs, /api/v1/auth/login, /api/v1/auth/register) skip validation.
    """

    PUBLIC_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/auth/login",
        "/api/v1/auth/register",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state.current_user = None
        path = request.url.path
        if any(path == p or path.startswith(p + "/") for p in self.PUBLIC_PATHS):
            return await call_next(request)
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return await call_next(request)
        token = auth[7:].strip()
        if not token:
            return await call_next(request)
        try:
            payload = JWTHelper.decode_token(token)
            if payload.get("type") != "access":
                return await call_next(request)
            user_id = int(payload.get("sub", 0))
            if not user_id:
                return await call_next(request)
            db = SessionLocal()
            try:
                user = db.get(User, user_id)
                if user and user.is_active:
                    request.state.current_user = user
            finally:
                db.close()
        except Exception:
            pass
        return await call_next(request)
