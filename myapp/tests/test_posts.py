"""
Post API tests. Rails equivalent: test/controllers/posts_controller_test.rb
"""

import pytest
from fastapi.testclient import TestClient


def test_list_posts_unauthenticated(client: TestClient, sample_post) -> None:
    """GET /posts without auth returns 200 (index is public)."""
    r = client.get("/api/v1/posts")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "data" in data
    assert "meta" in data


def test_list_posts_filter_published(client: TestClient, sample_post) -> None:
    """GET /posts?published=true returns only published."""
    r = client.get("/api/v1/posts?published=true")
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_get_post(authenticated_client: TestClient, sample_post) -> None:
    """GET /posts/:id returns 200."""
    r = authenticated_client.get(f"/api/v1/posts/{sample_post.id}")
    assert r.status_code == 200
    assert r.json()["data"]["title"] == "Test Post"


def test_create_post(authenticated_client: TestClient, sample_user) -> None:
    """POST /posts returns 201."""
    r = authenticated_client.post(
        "/api/v1/posts",
        json={"title": "New Post", "body": "Body here", "published": False},
    )
    assert r.status_code == 201
    assert r.json()["data"]["title"] == "New Post"


def test_update_post(authenticated_client: TestClient, sample_post) -> None:
    """PUT /posts/:id returns 200."""
    r = authenticated_client.put(
        f"/api/v1/posts/{sample_post.id}",
        json={"title": "Updated Title"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["title"] == "Updated Title"


def test_delete_post_soft(authenticated_client: TestClient, sample_post) -> None:
    """DELETE /posts/:id returns 200 (soft delete)."""
    r = authenticated_client.delete(f"/api/v1/posts/{sample_post.id}")
    assert r.status_code == 200
    assert r.json()["data"]["deleted"] is True
