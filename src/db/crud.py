"""CRUD operations for database models.

This module provides Create, Read, Update, Delete operations for
all database models. These are used by the API and agent.
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.db.models import Evaluation, Post, PostContent, Review


def create_post(db: Session, topic: str) -> Post:
    """Create a new post record.
    
    Args:
        db: Database session
        topic: Post topic
        
    Returns:
        Created Post instance
    """
    post = Post(topic=topic, status="draft")
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_post(db: Session, post_id: int) -> Optional[Post]:
    """Get a post by ID.
    
    Args:
        db: Database session
        post_id: Post ID
        
    Returns:
        Post instance or None
    """
    return db.query(Post).filter(Post.id == post_id).first()


def get_posts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
) -> List[Post]:
    """Get list of posts with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        status: Optional status filter
        
    Returns:
        List of Post instances
    """
    query = db.query(Post)
    if status:
        query = query.filter(Post.status == status)
    return query.offset(skip).limit(limit).all()


def update_post_status(db: Session, post_id: int, status: str) -> Optional[Post]:
    """Update post status.
    
    Args:
        db: Database session
        post_id: Post ID
        status: New status
        
    Returns:
        Updated Post instance or None
    """
    post = get_post(db, post_id)
    if post:
        post.status = status
        db.commit()
        db.refresh(post)
    return post


def update_post_image(db: Session, post_id: int, image_url: str) -> Optional[Post]:
    """Update post image URL.
    
    Args:
        db: Database session
        post_id: Post ID
        image_url: Image URL/path
        
    Returns:
        Updated Post instance or None
    """
    post = get_post(db, post_id)
    if post:
        post.image_url = image_url
        db.commit()
        db.refresh(post)
    return post


def create_post_content(
    db: Session,
    post_id: int,
    platform: str,
    content: str,
    metadata: Optional[dict] = None,
) -> PostContent:
    """Create platform-specific content for a post.
    
    Args:
        db: Database session
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
        metadata=metadata or {},
    )
    db.add(post_content)
    db.commit()
    db.refresh(post_content)
    return post_content


def get_post_contents(db: Session, post_id: int) -> List[PostContent]:
    """Get all content for a post.
    
    Args:
        db: Database session
        post_id: Post ID
        
    Returns:
        List of PostContent instances
    """
    return db.query(PostContent).filter(PostContent.post_id == post_id).all()


def create_review(
    db: Session,
    post_id: int,
    action: str,
    feedback: Optional[str] = None,
) -> Review:
    """Create a review record.
    
    Args:
        db: Database session
        post_id: Post ID
        action: Review action (approve, reject, edit)
        feedback: Optional feedback text
        
    Returns:
        Created Review instance
    """
    review = Review(post_id=post_id, action=action, feedback=feedback)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def create_evaluation(
    db: Session,
    post_id: int,
    metric_name: str,
    score: float,
    evaluator_type: str,
    metadata: Optional[dict] = None,
) -> Evaluation:
    """Create an evaluation record.
    
    Args:
        db: Database session
        post_id: Post ID
        metric_name: Metric name
        score: Numeric score
        evaluator_type: Evaluator type
        metadata: Additional metadata
        
    Returns:
        Created Evaluation instance
    """
    evaluation = Evaluation(
        post_id=post_id,
        metric_name=metric_name,
        score=score,
        evaluator_type=evaluator_type,
        metadata=metadata or {},
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)
    return evaluation


def get_evaluations(db: Session, post_id: int) -> List[Evaluation]:
    """Get all evaluations for a post.
    
    Args:
        db: Database session
        post_id: Post ID
        
    Returns:
        List of Evaluation instances
    """
    return db.query(Evaluation).filter(Evaluation.post_id == post_id).all()

