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


class TestGeneratePostEndpoint:
    """Tests for POST /api/posts/generate endpoint."""

    def test_generate_post_success(self, client, db, monkeypatch):
        """Test successful post generation initiation."""
        # Mock the workflow to avoid actual execution
        mock_workflow_called = []

        class MockWorkflow:
            async def ainvoke(self, state, config):
                mock_workflow_called.append((state, config))

        # Mock at the graph module level since workflow is imported inside the function
        monkeypatch.setattr("src.agent.graph.workflow", MockWorkflow())

        response = client.post("/api/posts/generate", json={"topic": "AI in healthcare"})

        assert response.status_code == 200
        data = response.json()
        assert "post_id" in data
        assert data["status"] == "generating"
        assert "message" in data

        # Verify post was created in database
        post_repo = PostRepository(db)
        post = post_repo.get_by_id(data["post_id"])
        assert post is not None
        assert post.topic == "AI in healthcare"
        assert post.status == "generating"

    def test_generate_post_empty_topic(self, client, db):
        """Test generation with empty topic."""
        response = client.post("/api/posts/generate", json={"topic": ""})

        # Should fail validation
        assert response.status_code == 422


class TestGetPostEndpoint:
    """Tests for GET /api/posts/{post_id} endpoint."""

    def test_get_post_success(self, client, sample_post):
        """Test getting a post by ID."""
        post_id = sample_post.id
        response = client.get(f"/api/posts/{post_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["post_id"] == post_id
        assert data["topic"] == sample_post.topic
        assert data["status"] == sample_post.status
        assert "linkedin_post" in data
        assert "instagram_post" in data
        assert "wordpress_post" in data

    def test_get_post_not_found(self, client, db):
        """Test getting a non-existent post."""
        response = client.get("/api/posts/99999")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_post_no_content(self, client, db):
        """Test getting a post with no content."""
        post_repo = PostRepository(db)
        post = post_repo.create(topic="Empty post")

        response = client.get(f"/api/posts/{post.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["linkedin_post"] is None
        assert data["instagram_post"] is None
        assert data["wordpress_post"] is None


class TestListPostsEndpoint:
    """Tests for GET /api/posts endpoint."""

    def test_list_posts_success(self, client, db):
        """Test listing all posts."""
        # Create multiple posts
        post_repo = PostRepository(db)
        post1 = post_repo.create(topic="AI topic", status="completed")
        post2 = post_repo.create(topic="ML topic", status="draft")

        response = client.get("/api/posts")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_posts_with_pagination(self, client, db):
        """Test listing posts with pagination."""
        # Create multiple posts
        post_repo = PostRepository(db)
        for i in range(5):
            post_repo.create(topic=f"Topic {i}")

        response = client.get("/api/posts?skip=2&limit=2")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_posts_with_status_filter(self, client, db):
        """Test listing posts filtered by status."""
        post_repo = PostRepository(db)
        post_repo.create(topic="Topic 1", status="completed")
        post_repo.create(topic="Topic 2", status="draft")
        post_repo.create(topic="Topic 3", status="completed")

        response = client.get("/api/posts?status=completed")

        assert response.status_code == 200
        data = response.json()
        assert all(post["status"] == "completed" for post in data)

    def test_list_posts_empty(self, client, db):
        """Test listing when no posts exist."""
        response = client.get("/api/posts")

        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestApprovePostEndpoint:
    """Tests for POST /api/posts/{post_id}/approve endpoint."""

    def test_approve_post_success(self, client, db, monkeypatch):
        """Test successful post approval."""
        # Create a post in pending_review state
        post_repo = PostRepository(db)
        post = post_repo.create(topic="Test topic")
        post = post_repo.update_status(post.id, "pending_review")

        # Mock the workflow
        mock_workflow_called = []

        class MockWorkflow:
            async def aget_state(self, config):
                class State:
                    values = {"approval_status": "pending_review"}

                return State()

            async def ainvoke(self, state, config):
                mock_workflow_called.append((state, config))

        # Mock at the graph module level since workflow is imported inside the function
        monkeypatch.setattr("src.agent.graph.workflow", MockWorkflow())

        response = client.post(f"/api/posts/{post.id}/approve")

        assert response.status_code == 200
        data = response.json()
        assert data["post_id"] == post.id
        assert data["status"] == "approved"

    def test_approve_post_not_found(self, client, db):
        """Test approving a non-existent post."""
        response = client.post("/api/posts/99999/approve")

        assert response.status_code == 404

    def test_approve_post_wrong_status(self, client, db):
        """Test approving a post not in review state."""
        post_repo = PostRepository(db)
        post = post_repo.create(topic="Test topic", status="draft")

        response = client.post(f"/api/posts/{post.id}/approve")

        assert response.status_code == 400
        assert "not in review state" in response.json()["detail"]


class TestRejectPostEndpoint:
    """Tests for POST /api/posts/{post_id}/reject endpoint."""

    def test_reject_post_success(self, client, db, monkeypatch):
        """Test successful post rejection."""
        # Create a post in pending_review state
        post_repo = PostRepository(db)
        post = post_repo.create(topic="Test topic")
        post = post_repo.update_status(post.id, "pending_review")

        # Mock the workflow
        mock_workflow_called = []

        class MockWorkflow:
            async def aget_state(self, config):
                class State:
                    values = {"approval_status": "pending_review"}

                return State()

            async def ainvoke(self, state, config):
                mock_workflow_called.append((state, config))

        # Mock at the graph module level since workflow is imported inside the function
        monkeypatch.setattr("src.agent.graph.workflow", MockWorkflow())

        response = client.post(
            f"/api/posts/{post.id}/reject",
            json={"feedback": "Please make it more engaging"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["post_id"] == post.id
        assert data["status"] == "rejected"

    def test_reject_post_not_found(self, client, db):
        """Test rejecting a non-existent post."""
        response = client.post(
            "/api/posts/99999/reject", json={"feedback": "Some feedback"}
        )

        assert response.status_code == 404

    def test_reject_post_wrong_status(self, client, db):
        """Test rejecting a post not in review state."""
        post_repo = PostRepository(db)
        post = post_repo.create(topic="Test topic", status="draft")

        response = client.post(
            f"/api/posts/{post.id}/reject", json={"feedback": "Some feedback"}
        )

        assert response.status_code == 400

    def test_reject_post_missing_feedback(self, client, db):
        """Test rejecting without providing feedback."""
        post_repo = PostRepository(db)
        post = post_repo.create(topic="Test topic", status="pending_review")

        response = client.post(f"/api/posts/{post.id}/reject", json={})

        assert response.status_code == 422  # Validation error


class TestEditPostEndpoint:
    """Tests for POST /api/posts/{post_id}/edit endpoint."""

    def test_edit_post_success(self, client, sample_post):
        """Test successful content editing."""
        new_content = json.dumps({"text": "Updated content", "hashtags": ["new"]})

        response = client.post(
            f"/api/posts/{sample_post.id}/edit",
            json={"platform": "linkedin", "content": new_content},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["post_id"] == sample_post.id
        assert data["platform"] == "linkedin"
        assert data["status"] == "updated"

    def test_edit_post_invalid_platform(self, client, sample_post):
        """Test editing with invalid platform."""
        response = client.post(
            f"/api/posts/{sample_post.id}/edit",
            json={"platform": "invalid", "content": "{}"},
        )

        assert response.status_code == 400
        assert "Invalid platform" in response.json()["detail"]

    def test_edit_post_not_found(self, client, db):
        """Test editing a non-existent post."""
        response = client.post(
            "/api/posts/99999/edit",
            json={"platform": "linkedin", "content": "{}"},
        )

        assert response.status_code == 404

    def test_edit_post_create_new_content(self, client, db):
        """Test editing creates content if it doesn't exist."""
        post_repo = PostRepository(db)
        post = post_repo.create(topic="Test topic")

        new_content = json.dumps({"text": "New content"})

        response = client.post(
            f"/api/posts/{post.id}/edit",
            json={"platform": "linkedin", "content": new_content},
        )

        assert response.status_code == 200


class TestGetImageEndpoint:
    """Tests for GET /api/posts/{post_id}/image endpoint."""

    def test_get_image_not_found_post(self, client, db):
        """Test getting image for non-existent post."""
        response = client.get("/api/posts/99999/image")

        assert response.status_code == 404

    def test_get_image_no_image(self, client, db):
        """Test getting image when no image exists."""
        post_repo = PostRepository(db)
        post = post_repo.create(topic="Test topic")

        response = client.get(f"/api/posts/{post.id}/image")

        assert response.status_code == 404
        assert "Image not found" in response.json()["detail"]
