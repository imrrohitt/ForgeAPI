"""
Central route definitions. Rails equivalent: config/routes.rb
Single file where all routes are registered. Uses resources() and namespace().
"""

import asyncio
from typing import Callable

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from app.controllers.users_controller import UsersController
from app.controllers.posts_controller import PostsController
from app.controllers.auth_controller import AuthController


def _wrap(
    controller_cls: type,
    action: str,
    handler: Callable,
    run_before: bool = True,
) -> Callable:
    """Run before_actions then call controller action. Return response."""

    async def _async_wrapper(
        request: Request,
        db: Session = Depends(get_db),
        **path_params: int | str,
    ):
        request.state.path_params = path_params
        ctrl = controller_cls(request=request, db=db)
        if run_before:
            controller_cls._run_before_actions(ctrl, action)
        result = handler(ctrl)
        if asyncio.iscoroutine(result):
            return await result
        return result

    return _async_wrapper


def resources(
    app_or_router: "APIRouter | FastAPI",
    path: str,
    controller_cls: type,
    only: list[str] | None = None,
) -> None:
    """
    Register REST resource routes: index, show, create, update, destroy.
    GET path -> index, POST path -> create, GET path/{id} -> show, PUT path/{id} -> update, DELETE path/{id} -> destroy.
    """
    only = only or ["index", "show", "create", "update", "destroy"]
    add = app_or_router.get if hasattr(app_or_router, "get") else app_or_router.add_api_route
    if "index" in only:
        app_or_router.add_api_route(
            path,
            _wrap(controller_cls, "index", lambda c: c.index()),
            methods=["GET"],
        )
    if "create" in only:
        app_or_router.add_api_route(
            path,
            _wrap(controller_cls, "create", lambda c: c.create()),
            methods=["POST"],
        )
    if "show" in only:
        app_or_router.add_api_route(
            f"{path}/{{id:int}}",
            _wrap(controller_cls, "show", lambda c: c.show()),
            methods=["GET"],
        )
    if "update" in only:
        app_or_router.add_api_route(
            f"{path}/{{id:int}}",
            _wrap(controller_cls, "update", lambda c: c.update()),
            methods=["PUT"],
        )
    if "destroy" in only:
        app_or_router.add_api_route(
            f"{path}/{{id:int}}",
            _wrap(controller_cls, "destroy", lambda c: c.destroy()),
            methods=["DELETE"],
        )


def namespace(app: "FastAPI", prefix: str):
    """Context manager: yield a router with prefix, then include it in app."""
    router = APIRouter(prefix=prefix)
    yield router
    app.include_router(router)


def draw_routes(app: "FastAPI") -> None:
    """
    Register all routes. Structure:
    # —— Auth ———
    POST   /api/v1/auth/login
    POST   /api/v1/auth/register
    POST   /api/v1/auth/logout
    GET    /api/v1/auth/me
    POST   /api/v1/auth/refresh
    # —— Users ———
    GET    /api/v1/users
    POST   /api/v1/users
    GET    /api/v1/users/{id}
    PUT    /api/v1/users/{id}
    DELETE /api/v1/users/{id}
    # —— Posts ———
    GET    /api/v1/posts
    POST   /api/v1/posts
    GET    /api/v1/posts/{id}
    PUT    /api/v1/posts/{id}
    DELETE /api/v1/posts/{id}
    """
    from fastapi import FastAPI
    auth_ctrl = AuthController
    users_ctrl = UsersController
    posts_ctrl = PostsController

    with namespace(app, "/api/v1") as router:
        # —— Auth ———
        router.add_api_route(
            "/auth/login",
            _wrap(auth_ctrl, "login", lambda c: c.login()),
            methods=["POST"],
        )
        router.add_api_route(
            "/auth/register",
            _wrap(auth_ctrl, "register", lambda c: c.register()),
            methods=["POST"],
        )
        router.add_api_route(
            "/auth/logout",
            _wrap(auth_ctrl, "logout", lambda c: c.logout()),
            methods=["POST"],
        )
        router.add_api_route(
            "/auth/me",
            _wrap(auth_ctrl, "me", lambda c: c.me()),
            methods=["GET"],
        )
        router.add_api_route(
            "/auth/refresh",
            _wrap(auth_ctrl, "refresh", lambda c: c.refresh()),
            methods=["POST"],
        )
        # —— Users ———
        resources(router, "/users", users_ctrl)
        # —— Posts ———
        resources(router, "/posts", posts_ctrl)
