"""
Database engine and session management.
Rails equivalent: config/database.rb + ActiveRecord connection.
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

from config.settings import get_settings


settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    echo=settings.DEBUG and settings.APP_ENV == "development",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base. Rails equivalent: ApplicationRecord base."""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a DB session. Rails equivalent: ActiveRecord connection per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
