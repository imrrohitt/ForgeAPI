"""
Auth API tests. Rails equivalent: test/controllers/sessions_controller_test.rb
"""

import pytest
from fastapi.testclient import TestClient


def test_register(client: TestClient, db) -> None:
    """POST /auth/register returns 201 and tokens."""
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": "authuser@example.com",
            "name": "Auth User",
            "password": "password123",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["success"] is True
    assert "data" in data
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


def test_login_valid(client: TestClient, sample_user) -> None:
    """POST /auth/login with valid credentials returns 200 and tokens."""
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_login_invalid_password(client: TestClient, sample_user) -> None:
    """POST /auth/login with wrong password returns 401."""
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "wrong"},
    )
    assert r.status_code == 401


def test_me(authenticated_client: TestClient, sample_user) -> None:
    """GET /auth/me returns 200 and current user."""
    r = authenticated_client.get("/api/v1/auth/me")
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["data"]["email"] == "user@example.com"


def test_refresh_token(client: TestClient, sample_user) -> None:
    """POST /auth/refresh returns 200 and new access token."""
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert login.status_code == 200
    refresh_token = login.json()["data"]["refresh_token"]
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    assert "access_token" in r.json()["data"]
