"""Database connection and session management.

This module handles database connections, session creation, and
provides utilities for database operations.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import settings
from src.db.models import Base

# Create engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using
    echo=settings.environment == "development",  # Log SQL in dev
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """Get database session for dependency injection.

    This is used as a FastAPI dependency to provide database sessions
    to route handlers. The session is automatically closed after use.

    Yields:
        Database session

    Example:
        @app.get("/posts")
        def get_posts(db: Session = Depends(get_db)):
            return db.query(Post).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables.

    Creates all tables defined in models.py if they don't exist.
    Note: This is for development only. Use Alembic migrations in production.
    """
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """Drop all database tables.

    WARNING: This deletes all data! Only use for testing.
    """
    Base.metadata.drop_all(bind=engine)
