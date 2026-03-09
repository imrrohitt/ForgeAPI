"""
User API tests. Rails equivalent: test/controllers/users_controller_test.rb
"""

import pytest
from fastapi.testclient import TestClient


def test_list_users_unauthenticated(client: TestClient) -> None:
    """GET /users without token returns 401."""
    r = client.get("/api/v1/users")
    assert r.status_code == 401


def test_list_users_authenticated(authenticated_client: TestClient) -> None:
    """GET /users with valid token returns 200 with pagination."""
    r = authenticated_client.get("/api/v1/users")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "data" in data
    assert "meta" in data
    assert "page" in data["meta"]
    assert "total" in data["meta"]


def test_create_user(client: TestClient, db) -> None:
    """POST /users creates user (requires auth - so we register first then list)."""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "name": "New User",
            "password": "password123",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["email"] == "newuser@example.com"
    assert data["data"]["name"] == "New User"
    assert "access_token" in data["data"] or "access_token" in data.get("data", {})


def test_create_user_duplicate_email(client: TestClient, sample_user) -> None:
    """Register again with same email returns 422."""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "user@example.com",
            "name": "Duplicate",
            "password": "password123",
        },
    )
    assert r.status_code in (422, 400)


def test_get_user(authenticated_client: TestClient, sample_user) -> None:
    """GET /users/:id returns 200."""
    r = authenticated_client.get(f"/api/v1/users/{sample_user.id}")
    assert r.status_code == 200
    assert r.json()["data"]["email"] == "user@example.com"


def test_get_user_not_found(authenticated_client: TestClient) -> None:
    """GET /users/99999 returns 404."""
    r = authenticated_client.get("/api/v1/users/99999")
    assert r.status_code == 404


def test_update_user(authenticated_client: TestClient, sample_user) -> None:
    """PUT /users/:id returns 200."""
    r = authenticated_client.put(
        f"/api/v1/users/{sample_user.id}",
        json={"name": "Updated Name"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["name"] == "Updated Name"


def test_delete_user_as_admin(client: TestClient, admin_user, sample_user) -> None:
    """DELETE /users/:id as admin returns 200."""
    r = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "Admin1234!"})
    assert r.status_code == 200
    token = r.json()["data"]["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    r = client.delete(f"/api/v1/users/{sample_user.id}")
    assert r.status_code == 200


def test_delete_user_as_non_admin(authenticated_client: TestClient, sample_user, admin_user) -> None:
    """DELETE /users/:id as non-admin returns 403 (cannot delete another user)."""
    # authenticated_client is regular user; try to delete admin
    r = authenticated_client.delete(f"/api/v1/users/{admin_user.id}")
    assert r.status_code == 403
