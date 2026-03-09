"""
Pytest fixtures: test db, client, authenticated_client, sample_user, sample_post, admin_user.
Rails equivalent: test/test_helper.rb + fixtures
"""

import os
import sys

# Use SQLite for tests so app loads without PostgreSQL
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "sqlite:///:memory:",
)

from config.database import Base, get_db
from app.models.user import User
from app.models.post import Post
from main import app


if "sqlite" in TEST_DATABASE_URL:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Session:
    """Fresh DB session per test. Creates tables."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client(db: Session) -> TestClient:
    """TestClient with overridden get_db."""
    return TestClient(app)


@pytest.fixture
def sample_user(db: Session) -> User:
    """Create a regular user for tests."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        email="user@example.com",
        name="Test User",
        hashed_password=pwd_context.hash("password123"),
        role="user",
        is_active=True,
    )
    user.save(db)
    return user


@pytest.fixture
def admin_user(db: Session) -> User:
    """Create an admin user for tests."""
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    user = User(
        email="admin@example.com",
        name="Admin",
        hashed_password=pwd_context.hash("Admin1234!"),
        role="admin",
        is_active=True,
    )
    user.save(db)
    return user


@pytest.fixture
def sample_post(db: Session, sample_user: User) -> Post:
    """Create a sample post."""
    post = Post(
        title="Test Post",
        body="Body of test post",
        user_id=sample_user.id,
        published=True,
    )
    post.save(db)
    return post


def get_token_for_user(client: TestClient, email: str, password: str) -> str:
    """Login and return access_token."""
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["data"]["access_token"]


@pytest.fixture
def authenticated_client(client: TestClient, sample_user: User) -> TestClient:
    """Client with Authorization header set for sample_user."""
    token = get_token_for_user(client, "user@example.com", "password123")
    client.headers["Authorization"] = f"Bearer {token}"
    return client
