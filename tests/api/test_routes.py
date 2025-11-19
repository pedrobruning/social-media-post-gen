"""Tests for API route handlers."""

import json
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set required environment variables before importing app
os.environ["OPENROUTER_API_KEY"] = "test-key-123"

from src.api.main import create_app
from src.db.database import Base, get_db
from src.db.repositories import PostContentRepository, PostRepository

# Test database setup - use shared memory so all connections see the same database
SQLALCHEMY_DATABASE_URL = "sqlite:///file::memory:?cache=shared&uri=true"


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh database engine for each test."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "uri": True}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db(db_engine):
    """Create a fresh database session for each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def client(db, db_engine, monkeypatch):
    """Create a test client with database dependency override."""
    # Create session factory for the test database
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    app = create_app()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Register routes
    from src.api.routes import router

    app.include_router(router, prefix="/api")

    # Mock SessionLocal in the database module to use test database session factory
    monkeypatch.setattr("src.db.database.SessionLocal", TestingSessionLocal)

    return TestClient(app)


@pytest.fixture
def sample_post(db):
    """Create a sample post for testing."""
    post_repo = PostRepository(db)
    content_repo = PostContentRepository(db)

    # Create post
    post = post_repo.create(topic="Test topic about AI")
    post = post_repo.update_status(post.id, "completed")

    # Store post_id to avoid detached instance issues
    post_id = post.id

    # Create content for all platforms (as JSON strings)
    linkedin_content = {
        "text": "Professional post about AI and machine learning.",
        "hashtags": ["AI", "ML", "Tech"],
        "image_description": "AI concept visualization",
    }

    instagram_content = {
        "caption": "Amazing AI content! Check this out.",
        "hashtags": ["#AI", "#ML", "#Tech", "#Innovation"],
        "image_description": "AI concept visualization",
    }

    wordpress_content = {
        "title": "Understanding AI",
        "sections": [{"type": "paragraph", "content": "Introduction to AI..."}],
        "seo_description": "Learn about AI",
        "featured_image": "image_url",
    }

    # Store as JSON strings
    content_repo.create(post_id, "linkedin", json.dumps(linkedin_content))
    content_repo.create(post_id, "instagram", json.dumps(instagram_content))
    content_repo.create(post_id, "wordpress", json.dumps(wordpress_content))

    # Refresh to get updated data
    db.refresh(post)

    return post


class TestEvaluateEndpoint:
    """Tests for POST /api/evaluate/{post_id} endpoint."""

    def test_evaluate_post_success(self, client, sample_post):
        """Test successful post evaluation."""
        post_id = sample_post.id
        response = client.post(f"/api/evaluate/{post_id}")

        assert response.status_code == 202
        data = response.json()
        assert data["post_id"] == post_id
        assert data["status"] == "evaluation_started"
        assert "message" in data

    def test_evaluate_post_not_found(self, client, db):
        """Test evaluation of non-existent post."""
        # Note: db parameter ensures database tables are created
        response = client.post("/api/evaluate/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_evaluate_post_no_content(self, client, db):
        """Test evaluation of post without content."""
        post_repo = PostRepository(db)
        post = post_repo.create(topic="Empty post")

        response = client.post(f"/api/evaluate/{post.id}")

        # Should still accept the request but may not produce evaluations
        assert response.status_code in [202, 400]

    def test_evaluate_post_invalid_id(self, client, db):
        """Test evaluation with invalid post ID."""
        # Note: db parameter ensures database tables are created
        response = client.post("/api/evaluate/invalid")

        assert response.status_code == 422  # Validation error


class TestGetEvaluationsEndpoint:
    """Tests for GET /api/posts/{post_id}/evaluations endpoint."""

    def test_get_evaluations_success(self, client, sample_post):
        """Test getting evaluations for a post."""
        post_id = sample_post.id

        # Just get evaluations (no need to trigger evaluation first for this test)
        response = client.get(f"/api/posts/{post_id}/evaluations")

        assert response.status_code == 200
        data = response.json()
        assert data["post_id"] == post_id
        assert "evaluations" in data
        # No evaluations exist yet, so should be empty
        assert data["evaluations"] == []

    def test_get_evaluations_not_found(self, client, db):
        """Test getting evaluations for non-existent post."""
        # Note: db parameter ensures database tables are created
        response = client.get("/api/posts/99999/evaluations")

        assert response.status_code == 404

    def test_get_evaluations_no_evaluations(self, client, sample_post):
        """Test getting evaluations when none exist."""
        post_id = sample_post.id
        response = client.get(f"/api/posts/{post_id}/evaluations")

        assert response.status_code == 200
        data = response.json()
        assert data["evaluations"] == []
