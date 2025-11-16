"""Repository pattern implementation for database models.

This module provides repository classes for each model, encapsulating
all database operations with a clean interface.
"""

from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import Evaluation, Post, PostContent, Review


class PostRepository:
    """Repository for Post model operations.

    Handles all database operations related to posts, including
    creating, reading, updating, and deleting post records.
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create(self, topic: str, status: str = "draft") -> Post:
        """Create a new post.

        Args:
            topic: Post topic
            status: Initial status (default: draft)

        Returns:
            Created Post instance
        """
        post = Post(topic=topic, status=status)
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post

    def get_by_id(self, post_id: int) -> Post | None:
        """Get a post by ID.

        Args:
            post_id: Post ID

        Returns:
            Post instance or None if not found
        """
        return self.db.query(Post).filter(Post.id == post_id).first()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
    ) -> list[Post]:
        """Get list of posts with optional filtering.

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return
            status: Optional status filter

        Returns:
            List of Post instances
        """
        query = self.db.query(Post)
        if status:
            query = query.filter(Post.status == status)
        return query.offset(skip).limit(limit).all()

    def update_status(self, post_id: int, status: str) -> Post | None:
        """Update post status.

        Args:
            post_id: Post ID
            status: New status

        Returns:
            Updated Post instance or None if not found
        """
        post = self.get_by_id(post_id)
        if post:
            post.status = status
            post.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(post)
        return post

    def update_image_url(self, post_id: int, image_url: str) -> Post | None:
        """Update post image URL.

        Args:
            post_id: Post ID
            image_url: Image URL/path

        Returns:
            Updated Post instance or None if not found
        """
        post = self.get_by_id(post_id)
        if post:
            post.image_url = image_url
            post.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(post)
        return post

    def delete(self, post_id: int) -> bool:
        """Delete a post.

        Args:
            post_id: Post ID

        Returns:
            True if deleted, False if not found
        """
        post = self.get_by_id(post_id)
        if post:
            self.db.delete(post)
            self.db.commit()
            return True
        return False

    def count_by_status(self, status: str) -> int:
        """Count posts by status.

        Args:
            status: Status to count

        Returns:
            Number of posts with given status
        """
        return self.db.query(Post).filter(Post.status == status).count()


class PostContentRepository:
    """Repository for PostContent model operations.

    Handles all database operations related to platform-specific content.
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create(
        self,
        post_id: int,
        platform: str,
        content: str,
        metadata: dict | None = None,
    ) -> PostContent:
        """Create platform-specific content.

        Args:
            post_id: Post ID
            platform: Platform name (linkedin, instagram, wordpress)
            content: Content text
            metadata: Additional metadata

        Returns:
            Created PostContent instance
        """
        post_content = PostContent(
            post_id=post_id,
            platform=platform,
            content=content,
            extra_metadata=metadata or {},
        )
        self.db.add(post_content)
        self.db.commit()
        self.db.refresh(post_content)
        return post_content

    def get_by_post_id(self, post_id: int) -> list[PostContent]:
        """Get all content for a post.

        Args:
            post_id: Post ID

        Returns:
            List of PostContent instances
        """
        return self.db.query(PostContent).filter(PostContent.post_id == post_id).all()

    def get_by_post_and_platform(
        self,
        post_id: int,
        platform: str,
    ) -> PostContent | None:
        """Get content for a specific post and platform.

        Args:
            post_id: Post ID
            platform: Platform name

        Returns:
            PostContent instance or None
        """
        return (
            self.db.query(PostContent)
            .filter(
                PostContent.post_id == post_id,
                PostContent.platform == platform,
            )
            .first()
        )

    def update_content(
        self,
        post_id: int,
        platform: str,
        content: str,
        metadata: dict | None = None,
    ) -> PostContent | None:
        """Update content for a platform.

        Args:
            post_id: Post ID
            platform: Platform name
            content: New content
            metadata: Updated metadata

        Returns:
            Updated PostContent or None
        """
        post_content = self.get_by_post_and_platform(post_id, platform)
        if post_content:
            post_content.content = content
            if metadata:
                post_content.extra_metadata = metadata
            self.db.commit()
            self.db.refresh(post_content)
        return post_content

    def delete_by_post_id(self, post_id: int) -> int:
        """Delete all content for a post.

        Args:
            post_id: Post ID

        Returns:
            Number of records deleted
        """
        count = self.db.query(PostContent).filter(PostContent.post_id == post_id).delete()
        self.db.commit()
        return count


class ReviewRepository:
    """Repository for Review model operations.

    Handles all database operations related to human reviews.
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create(
        self,
        post_id: int,
        action: str,
        feedback: str | None = None,
    ) -> Review:
        """Create a review record.

        Args:
            post_id: Post ID
            action: Review action (approve, reject, edit)
            feedback: Optional feedback text

        Returns:
            Created Review instance
        """
        review = Review(
            post_id=post_id,
            action=action,
            feedback=feedback,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_by_post_id(self, post_id: int) -> list[Review]:
        """Get all reviews for a post.

        Args:
            post_id: Post ID

        Returns:
            List of Review instances
        """
        return (
            self.db.query(Review)
            .filter(Review.post_id == post_id)
            .order_by(Review.reviewed_at.desc())
            .all()
        )

    def get_latest_review(self, post_id: int) -> Review | None:
        """Get the most recent review for a post.

        Args:
            post_id: Post ID

        Returns:
            Latest Review instance or None
        """
        return (
            self.db.query(Review)
            .filter(Review.post_id == post_id)
            .order_by(Review.reviewed_at.desc())
            .first()
        )

    def get_approval_rate(self) -> float:
        """Calculate overall approval rate.

        Returns:
            Approval rate (0-1)
        """
        total = self.db.query(Review).count()
        if total == 0:
            return 0.0

        approved = self.db.query(Review).filter(Review.action == "approve").count()
        return approved / total


class EvaluationRepository:
    """Repository for Evaluation model operations.

    Handles all database operations related to content evaluations.
    """

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create(
        self,
        post_id: int,
        metric_name: str,
        score: float,
        evaluator_type: str,
        metadata: dict | None = None,
    ) -> Evaluation:
        """Create an evaluation record.

        Args:
            post_id: Post ID
            metric_name: Metric name
            score: Numeric score
            evaluator_type: Evaluator type (quality, platform, llm_judge)
            metadata: Additional metadata

        Returns:
            Created Evaluation instance
        """
        evaluation = Evaluation(
            post_id=post_id,
            metric_name=metric_name,
            score=score,
            evaluator_type=evaluator_type,
            extra_metadata=metadata or {},
        )
        self.db.add(evaluation)
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation

    def get_by_post_id(self, post_id: int) -> list[Evaluation]:
        """Get all evaluations for a post.

        Args:
            post_id: Post ID

        Returns:
            List of Evaluation instances
        """
        return (
            self.db.query(Evaluation)
            .filter(Evaluation.post_id == post_id)
            .order_by(Evaluation.created_at.desc())
            .all()
        )

    def get_by_metric(
        self,
        post_id: int,
        metric_name: str,
    ) -> Evaluation | None:
        """Get evaluation for a specific metric.

        Args:
            post_id: Post ID
            metric_name: Metric name

        Returns:
            Evaluation instance or None
        """
        return (
            self.db.query(Evaluation)
            .filter(
                Evaluation.post_id == post_id,
                Evaluation.metric_name == metric_name,
            )
            .first()
        )

    def get_average_score_by_metric(self, metric_name: str) -> float:
        """Calculate average score for a metric across all posts.

        Args:
            metric_name: Metric name

        Returns:
            Average score
        """
        from sqlalchemy import func

        result = (
            self.db.query(func.avg(Evaluation.score))
            .filter(Evaluation.metric_name == metric_name)
            .scalar()
        )
        return float(result) if result else 0.0

    def delete_by_post_id(self, post_id: int) -> int:
        """Delete all evaluations for a post.

        Args:
            post_id: Post ID

        Returns:
            Number of records deleted
        """
        count = self.db.query(Evaluation).filter(Evaluation.post_id == post_id).delete()
        self.db.commit()
        return count
