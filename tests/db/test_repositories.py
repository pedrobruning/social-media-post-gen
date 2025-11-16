"""Tests for database repositories.

This module contains comprehensive tests for all repository classes following TDD principles.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import Base, Post, PostContent, Review, Evaluation
from src.db.repositories import (
    PostRepository,
    PostContentRepository,
    ReviewRepository,
    EvaluationRepository,
)


# ===== Test Database Setup =====

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test.

    This fixture:
    1. Creates an in-memory SQLite database
    2. Creates all tables
    3. Yields a session for the test
    4. Cleans up after the test

    Yields:
        SQLAlchemy Session
    """
    # Create in-memory database (fast, isolated)
    engine = create_engine("sqlite:///:memory:")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session factory
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ===== PostRepository Tests =====

class TestPostRepository:
    """Tests for PostRepository class."""

    def test_create_post(self, db_session: Session):
        """Test creating a new post."""
        # Arrange
        repo = PostRepository(db_session)
        topic = "The Future of AI in Healthcare"

        # Act
        post = repo.create(topic=topic)

        # Assert
        assert post.id is not None
        assert post.topic == topic
        assert post.status == "draft"  # Default status
        assert post.image_url is None
        assert post.created_at is not None
        assert post.updated_at is not None

    def test_create_post_with_custom_status(self, db_session: Session):
        """Test creating a post with custom status."""
        # Arrange
        repo = PostRepository(db_session)

        # Act
        post = repo.create(topic="Test Topic", status="pending_review")

        # Assert
        assert post.status == "pending_review"

    def test_get_by_id_existing(self, db_session: Session):
        """Test retrieving an existing post by ID."""
        # Arrange
        repo = PostRepository(db_session)
        created_post = repo.create(topic="Test Topic")

        # Act
        retrieved_post = repo.get_by_id(created_post.id)

        # Assert
        assert retrieved_post is not None
        assert retrieved_post.id == created_post.id
        assert retrieved_post.topic == created_post.topic

    def test_get_by_id_nonexistent(self, db_session: Session):
        """Test retrieving a nonexistent post returns None."""
        # Arrange
        repo = PostRepository(db_session)

        # Act
        post = repo.get_by_id(999)

        # Assert
        assert post is None

    def test_get_all_empty(self, db_session: Session):
        """Test getting all posts when database is empty."""
        # Arrange
        repo = PostRepository(db_session)

        # Act
        posts = repo.get_all()

        # Assert
        assert posts == []

    def test_get_all_multiple_posts(self, db_session: Session):
        """Test getting all posts."""
        # Arrange
        repo = PostRepository(db_session)
        repo.create(topic="Post 1")
        repo.create(topic="Post 2")
        repo.create(topic="Post 3")

        # Act
        posts = repo.get_all()

        # Assert
        assert len(posts) == 3
        assert posts[0].topic == "Post 1"
        assert posts[1].topic == "Post 2"
        assert posts[2].topic == "Post 3"

    def test_get_all_with_pagination(self, db_session: Session):
        """Test pagination with skip and limit."""
        # Arrange
        repo = PostRepository(db_session)
        for i in range(10):
            repo.create(topic=f"Post {i}")

        # Act
        page_1 = repo.get_all(skip=0, limit=3)
        page_2 = repo.get_all(skip=3, limit=3)

        # Assert
        assert len(page_1) == 3
        assert len(page_2) == 3
        assert page_1[0].topic == "Post 0"
        assert page_2[0].topic == "Post 3"

    def test_get_all_with_status_filter(self, db_session: Session):
        """Test filtering posts by status."""
        # Arrange
        repo = PostRepository(db_session)
        repo.create(topic="Draft 1", status="draft")
        repo.create(topic="Approved 1", status="approved")
        repo.create(topic="Draft 2", status="draft")

        # Act
        draft_posts = repo.get_all(status="draft")
        approved_posts = repo.get_all(status="approved")

        # Assert
        assert len(draft_posts) == 2
        assert len(approved_posts) == 1
        assert all(p.status == "draft" for p in draft_posts)
        assert approved_posts[0].status == "approved"

    def test_update_status_existing(self, db_session: Session):
        """Test updating status of existing post."""
        # Arrange
        repo = PostRepository(db_session)
        post = repo.create(topic="Test", status="draft")
        original_updated_at = post.updated_at

        # Act (small delay to ensure different timestamp)
        import time
        time.sleep(0.01)
        updated_post = repo.update_status(post.id, "approved")

        # Assert
        assert updated_post is not None
        assert updated_post.status == "approved"
        assert updated_post.updated_at > original_updated_at

    def test_update_status_nonexistent(self, db_session: Session):
        """Test updating status of nonexistent post returns None."""
        # Arrange
        repo = PostRepository(db_session)

        # Act
        result = repo.update_status(999, "approved")

        # Assert
        assert result is None

    def test_update_image_url_existing(self, db_session: Session):
        """Test updating image URL."""
        # Arrange
        repo = PostRepository(db_session)
        post = repo.create(topic="Test")
        image_url = "/storage/images/12345.png"

        # Act
        updated_post = repo.update_image_url(post.id, image_url)

        # Assert
        assert updated_post is not None
        assert updated_post.image_url == image_url

    def test_update_image_url_nonexistent(self, db_session: Session):
        """Test updating image URL of nonexistent post."""
        # Arrange
        repo = PostRepository(db_session)

        # Act
        result = repo.update_image_url(999, "/path/to/image.png")

        # Assert
        assert result is None

    def test_delete_existing(self, db_session: Session):
        """Test deleting an existing post."""
        # Arrange
        repo = PostRepository(db_session)
        post = repo.create(topic="Test")

        # Act
        result = repo.delete(post.id)

        # Assert
        assert result is True
        assert repo.get_by_id(post.id) is None

    def test_delete_nonexistent(self, db_session: Session):
        """Test deleting a nonexistent post."""
        # Arrange
        repo = PostRepository(db_session)

        # Act
        result = repo.delete(999)

        # Assert
        assert result is False

    def test_count_by_status(self, db_session: Session):
        """Test counting posts by status."""
        # Arrange
        repo = PostRepository(db_session)
        repo.create(topic="Draft 1", status="draft")
        repo.create(topic="Draft 2", status="draft")
        repo.create(topic="Draft 3", status="draft")
        repo.create(topic="Approved 1", status="approved")

        # Act
        draft_count = repo.count_by_status("draft")
        approved_count = repo.count_by_status("approved")
        pending_count = repo.count_by_status("pending_review")

        # Assert
        assert draft_count == 3
        assert approved_count == 1
        assert pending_count == 0

    def test_cascade_delete(self, db_session: Session):
        """Test that deleting a post cascades to related content."""
        # Arrange
        post_repo = PostRepository(db_session)
        content_repo = PostContentRepository(db_session)

        post = post_repo.create(topic="Test")
        content_repo.create(post_id=post.id, platform="linkedin", content="Test content")

        # Act
        post_repo.delete(post.id)

        # Assert
        remaining_content = content_repo.get_by_post_id(post.id)
        assert remaining_content == []


# ===== PostContentRepository Tests =====

class TestPostContentRepository:
    """Tests for PostContentRepository class."""

    def test_create_content(self, db_session: Session):
        """Test creating platform-specific content."""
        # Arrange
        post_repo = PostRepository(db_session)
        content_repo = PostContentRepository(db_session)
        post = post_repo.create(topic="Test")

        # Act
        content = content_repo.create(
            post_id=post.id,
            platform="linkedin",
            content="Professional post for LinkedIn",
            metadata={"hashtags": ["AI", "ML"]},
        )

        # Assert
        assert content.id is not None
        assert content.post_id == post.id
        assert content.platform == "linkedin"
        assert content.content == "Professional post for LinkedIn"
        assert content.extra_metadata == {"hashtags": ["AI", "ML"]}
        assert content.created_at is not None

    def test_create_content_without_metadata(self, db_session: Session):
        """Test creating content without metadata."""
        # Arrange
        post_repo = PostRepository(db_session)
        content_repo = PostContentRepository(db_session)
        post = post_repo.create(topic="Test")

        # Act
        content = content_repo.create(
            post_id=post.id,
            platform="instagram",
            content="Visual content",
        )

        # Assert
        assert content.extra_metadata == {}

    def test_get_by_post_id(self, db_session: Session):
        """Test getting all content for a post."""
        # Arrange
        post_repo = PostRepository(db_session)
        content_repo = PostContentRepository(db_session)
        post = post_repo.create(topic="Test")

        content_repo.create(post_id=post.id, platform="linkedin", content="LinkedIn post")
        content_repo.create(post_id=post.id, platform="instagram", content="Instagram post")
        content_repo.create(post_id=post.id, platform="wordpress", content="WordPress article")

        # Act
        contents = content_repo.get_by_post_id(post.id)

        # Assert
        assert len(contents) == 3
        platforms = [c.platform for c in contents]
        assert "linkedin" in platforms
        assert "instagram" in platforms
        assert "wordpress" in platforms

    def test_get_by_post_and_platform(self, db_session: Session):
        """Test getting content for specific post and platform."""
        # Arrange
        post_repo = PostRepository(db_session)
        content_repo = PostContentRepository(db_session)
        post = post_repo.create(topic="Test")

        content_repo.create(post_id=post.id, platform="linkedin", content="LinkedIn post")
        content_repo.create(post_id=post.id, platform="instagram", content="Instagram post")

        # Act
        linkedin_content = content_repo.get_by_post_and_platform(post.id, "linkedin")
        wordpress_content = content_repo.get_by_post_and_platform(post.id, "wordpress")

        # Assert
        assert linkedin_content is not None
        assert linkedin_content.platform == "linkedin"
        assert linkedin_content.content == "LinkedIn post"
        assert wordpress_content is None

    def test_update_content(self, db_session: Session):
        """Test updating existing content."""
        # Arrange
        post_repo = PostRepository(db_session)
        content_repo = PostContentRepository(db_session)
        post = post_repo.create(topic="Test")

        original_content = content_repo.create(
            post_id=post.id,
            platform="linkedin",
            content="Original content",
            metadata={"version": 1},
        )

        # Act
        updated_content = content_repo.update_content(
            post_id=post.id,
            platform="linkedin",
            content="Updated content",
            metadata={"version": 2},
        )

        # Assert
        assert updated_content is not None
        assert updated_content.id == original_content.id
        assert updated_content.content == "Updated content"
        assert updated_content.extra_metadata == {"version": 2}

    def test_update_nonexistent_content(self, db_session: Session):
        """Test updating nonexistent content returns None."""
        # Arrange
        post_repo = PostRepository(db_session)
        content_repo = PostContentRepository(db_session)
        post = post_repo.create(topic="Test")

        # Act
        result = content_repo.update_content(
            post_id=post.id,
            platform="linkedin",
            content="New content",
        )

        # Assert
        assert result is None

    def test_delete_by_post_id(self, db_session: Session):
        """Test deleting all content for a post."""
        # Arrange
        post_repo = PostRepository(db_session)
        content_repo = PostContentRepository(db_session)
        post = post_repo.create(topic="Test")

        content_repo.create(post_id=post.id, platform="linkedin", content="LinkedIn")
        content_repo.create(post_id=post.id, platform="instagram", content="Instagram")

        # Act
        deleted_count = content_repo.delete_by_post_id(post.id)

        # Assert
        assert deleted_count == 2
        assert content_repo.get_by_post_id(post.id) == []


# ===== ReviewRepository Tests =====

class TestReviewRepository:
    """Tests for ReviewRepository class."""

    def test_create_review(self, db_session: Session):
        """Test creating a review."""
        # Arrange
        post_repo = PostRepository(db_session)
        review_repo = ReviewRepository(db_session)
        post = post_repo.create(topic="Test")

        # Act
        review = review_repo.create(
            post_id=post.id,
            action="approve",
            feedback="Looks great!",
        )

        # Assert
        assert review.id is not None
        assert review.post_id == post.id
        assert review.action == "approve"
        assert review.feedback == "Looks great!"
        assert review.reviewed_at is not None

    def test_create_review_without_feedback(self, db_session: Session):
        """Test creating a review without feedback."""
        # Arrange
        post_repo = PostRepository(db_session)
        review_repo = ReviewRepository(db_session)
        post = post_repo.create(topic="Test")

        # Act
        review = review_repo.create(post_id=post.id, action="approve")

        # Assert
        assert review.feedback is None

    def test_get_by_post_id(self, db_session: Session):
        """Test getting all reviews for a post."""
        # Arrange
        post_repo = PostRepository(db_session)
        review_repo = ReviewRepository(db_session)
        post = post_repo.create(topic="Test")

        review_repo.create(post_id=post.id, action="reject", feedback="Needs work")
        review_repo.create(post_id=post.id, action="edit", feedback="Minor changes")
        review_repo.create(post_id=post.id, action="approve", feedback="Perfect!")

        # Act
        reviews = review_repo.get_by_post_id(post.id)

        # Assert
        assert len(reviews) == 3
        # Should be ordered by reviewed_at desc (newest first)
        assert reviews[0].action == "approve"
        assert reviews[1].action == "edit"
        assert reviews[2].action == "reject"

    def test_get_latest_review(self, db_session: Session):
        """Test getting the most recent review."""
        # Arrange
        post_repo = PostRepository(db_session)
        review_repo = ReviewRepository(db_session)
        post = post_repo.create(topic="Test")

        review_repo.create(post_id=post.id, action="reject")
        review_repo.create(post_id=post.id, action="edit")
        latest = review_repo.create(post_id=post.id, action="approve")

        # Act
        retrieved_latest = review_repo.get_latest_review(post.id)

        # Assert
        assert retrieved_latest is not None
        assert retrieved_latest.id == latest.id
        assert retrieved_latest.action == "approve"

    def test_get_latest_review_no_reviews(self, db_session: Session):
        """Test getting latest review when none exist."""
        # Arrange
        post_repo = PostRepository(db_session)
        review_repo = ReviewRepository(db_session)
        post = post_repo.create(topic="Test")

        # Act
        result = review_repo.get_latest_review(post.id)

        # Assert
        assert result is None

    def test_get_approval_rate_no_reviews(self, db_session: Session):
        """Test approval rate with no reviews."""
        # Arrange
        review_repo = ReviewRepository(db_session)

        # Act
        rate = review_repo.get_approval_rate()

        # Assert
        assert rate == 0.0

    def test_get_approval_rate(self, db_session: Session):
        """Test calculating approval rate."""
        # Arrange
        post_repo = PostRepository(db_session)
        review_repo = ReviewRepository(db_session)

        post1 = post_repo.create(topic="Post 1")
        post2 = post_repo.create(topic="Post 2")
        post3 = post_repo.create(topic="Post 3")
        post4 = post_repo.create(topic="Post 4")

        review_repo.create(post_id=post1.id, action="approve")
        review_repo.create(post_id=post2.id, action="approve")
        review_repo.create(post_id=post3.id, action="approve")
        review_repo.create(post_id=post4.id, action="reject")

        # Act
        rate = review_repo.get_approval_rate()

        # Assert
        assert rate == 0.75  # 3 out of 4 approved


# ===== EvaluationRepository Tests =====

class TestEvaluationRepository:
    """Tests for EvaluationRepository class."""

    def test_create_evaluation(self, db_session: Session):
        """Test creating an evaluation."""
        # Arrange
        post_repo = PostRepository(db_session)
        eval_repo = EvaluationRepository(db_session)
        post = post_repo.create(topic="Test")

        # Act
        evaluation = eval_repo.create(
            post_id=post.id,
            metric_name="readability",
            score=8.5,
            evaluator_type="quality",
            metadata={"details": "Good structure"},
        )

        # Assert
        assert evaluation.id is not None
        assert evaluation.post_id == post.id
        assert evaluation.metric_name == "readability"
        assert evaluation.score == 8.5
        assert evaluation.evaluator_type == "quality"
        assert evaluation.extra_metadata == {"details": "Good structure"}
        assert evaluation.created_at is not None

    def test_get_by_post_id(self, db_session: Session):
        """Test getting all evaluations for a post."""
        # Arrange
        post_repo = PostRepository(db_session)
        eval_repo = EvaluationRepository(db_session)
        post = post_repo.create(topic="Test")

        eval_repo.create(post_id=post.id, metric_name="readability", score=8.5, evaluator_type="quality")
        eval_repo.create(post_id=post.id, metric_name="engagement", score=7.2, evaluator_type="llm_judge")
        eval_repo.create(post_id=post.id, metric_name="seo", score=9.0, evaluator_type="platform")

        # Act
        evaluations = eval_repo.get_by_post_id(post.id)

        # Assert
        assert len(evaluations) == 3
        metrics = [e.metric_name for e in evaluations]
        assert "readability" in metrics
        assert "engagement" in metrics
        assert "seo" in metrics

    def test_get_by_metric(self, db_session: Session):
        """Test getting evaluation for specific metric."""
        # Arrange
        post_repo = PostRepository(db_session)
        eval_repo = EvaluationRepository(db_session)
        post = post_repo.create(topic="Test")

        eval_repo.create(post_id=post.id, metric_name="readability", score=8.5, evaluator_type="quality")
        eval_repo.create(post_id=post.id, metric_name="engagement", score=7.2, evaluator_type="llm_judge")

        # Act
        readability_eval = eval_repo.get_by_metric(post.id, "readability")
        seo_eval = eval_repo.get_by_metric(post.id, "seo")

        # Assert
        assert readability_eval is not None
        assert readability_eval.score == 8.5
        assert seo_eval is None

    def test_get_average_score_by_metric(self, db_session: Session):
        """Test calculating average score for a metric."""
        # Arrange
        post_repo = PostRepository(db_session)
        eval_repo = EvaluationRepository(db_session)

        post1 = post_repo.create(topic="Post 1")
        post2 = post_repo.create(topic="Post 2")
        post3 = post_repo.create(topic="Post 3")

        eval_repo.create(post_id=post1.id, metric_name="readability", score=8.0, evaluator_type="quality")
        eval_repo.create(post_id=post2.id, metric_name="readability", score=9.0, evaluator_type="quality")
        eval_repo.create(post_id=post3.id, metric_name="readability", score=7.0, evaluator_type="quality")
        eval_repo.create(post_id=post1.id, metric_name="engagement", score=6.0, evaluator_type="llm_judge")

        # Act
        avg_readability = eval_repo.get_average_score_by_metric("readability")
        avg_engagement = eval_repo.get_average_score_by_metric("engagement")
        avg_nonexistent = eval_repo.get_average_score_by_metric("nonexistent")

        # Assert
        assert avg_readability == 8.0  # (8 + 9 + 7) / 3
        assert avg_engagement == 6.0
        assert avg_nonexistent == 0.0

    def test_delete_by_post_id(self, db_session: Session):
        """Test deleting all evaluations for a post."""
        # Arrange
        post_repo = PostRepository(db_session)
        eval_repo = EvaluationRepository(db_session)
        post = post_repo.create(topic="Test")

        eval_repo.create(post_id=post.id, metric_name="readability", score=8.5, evaluator_type="quality")
        eval_repo.create(post_id=post.id, metric_name="engagement", score=7.2, evaluator_type="llm_judge")

        # Act
        deleted_count = eval_repo.delete_by_post_id(post.id)

        # Assert
        assert deleted_count == 2
        assert eval_repo.get_by_post_id(post.id) == []
