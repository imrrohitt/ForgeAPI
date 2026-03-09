"""
Posts controller: index, show, create, update, destroy (soft delete).
Rails equivalent: app/controllers/posts_controller.rb
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.controllers.base_controller import BaseController, before_action
from app.controllers.concerns.authenticatable import Authenticatable
from app.models.post import Post
from app.schemas.post_schema import PostCreateSchema, PostUpdateSchema, PostResponseSchema
from app.services.post_service import PostService


class PostsController(BaseController, Authenticatable):
    """
    before_action: authenticate_user except index, show
    before_action: set_post, only show, update, destroy
    before_action: authorize_owner, only update, destroy
    """

    @before_action(only=["show", "update", "destroy"])
    def set_post(self) -> None:
        pid = int(self.request.path_params["id"])
        self._post = Post.find(self.db, pid)
        if self._post.deleted_at:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Post not found")

    @before_action(except_list=["index", "show"])
    def authenticate_user_filter(self) -> None:
        self.authenticate_user()

    @before_action(only=["update", "destroy"])
    def authorize_owner(self) -> None:
        self.require_owner(self._post)

    def index(self) -> JSONResponse:
        """GET /posts - paginated, filter ?published=true."""
        page = int(self.request.query_params.get("page", 1))
        per_page = int(self.request.query_params.get("per_page", 20))
        published_only = self.request.query_params.get("published", "").lower() == "true"
        svc = PostService(self.db)
        result = svc.list_posts(page=page, per_page=per_page, published_only=published_only)
        data = result["data"]
        items = [PostResponseSchema.model_validate(p) for p in data["data"]]
        return self.render_json([m.model_dump(mode="json") for m in items], meta=data["meta"])

    def show(self) -> JSONResponse:
        """GET /posts/:id."""
        post = getattr(self, "_post", None) or Post.find(self.db, int(self.request.path_params["id"]))
        if post.deleted_at:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Post not found")
        return self.render_json(PostResponseSchema.model_validate(post).model_dump(mode="json"))

    async def create(self) -> JSONResponse:
        """POST /posts."""
        body = await self.request.json()
        payload = PostCreateSchema.model_validate(body)
        svc = PostService(self.db)
        result = svc.create_post(self.current_user, payload)
        post = result["data"]
        return self.render_json(PostResponseSchema.model_validate(post).model_dump(mode="json"), status=201)

    async def update(self) -> JSONResponse:
        """PUT /posts/:id."""
        post = getattr(self, "_post", None) or Post.find(self.db, int(self.request.path_params["id"]))
        body = await self.request.json()
        payload = PostUpdateSchema.model_validate(body)
        svc = PostService(self.db)
        result = svc.update_post(post, payload)
        return self.render_json(PostResponseSchema.model_validate(result["data"]).model_dump(mode="json"))

    def destroy(self) -> JSONResponse:
        """DELETE /posts/:id - soft delete."""
        post = getattr(self, "_post", None) or Post.find(self.db, int(self.request.path_params["id"]))
        svc = PostService(self.db)
        svc.delete_post(post)
        return self.render_json({"deleted": True})
