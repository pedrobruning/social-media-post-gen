"""SQLAlchemy database models for social media posts.

This module defines the database schema using SQLAlchemy ORM.
All posts, content, reviews, and evaluations are stored here.
"""

from datetime import datetime
from typing import List

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Post(Base):
    """Main post record tracking the generation workflow.
    
    Attributes:
        id: Primary key
        topic: Original topic provided by user
        status: Current status (draft, pending_review, approved, rejected)
        image_url: Path/URL to generated image
        created_at: When the post was created
        updated_at: When the post was last updated
    """
    
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
        index=True,
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    
    # Relationships
    contents: Mapped[List["PostContent"]] = relationship(
        "PostContent",
        back_populates="post",
        cascade="all, delete-orphan",
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review",
        back_populates="post",
        cascade="all, delete-orphan",
    )
    evaluations: Mapped[List["Evaluation"]] = relationship(
        "Evaluation",
        back_populates="post",
        cascade="all, delete-orphan",
    )


class PostContent(Base):
    """Platform-specific content for a post.
    
    Attributes:
        id: Primary key
        post_id: Foreign key to Post
        platform: Platform name (linkedin, instagram, wordpress)
        content: The generated content text
        metadata: Additional platform-specific metadata (JSON)
        created_at: When the content was generated
    """
    
    __tablename__ = "post_contents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="contents")


class Review(Base):
    """Human review actions on posts.
    
    Attributes:
        id: Primary key
        post_id: Foreign key to Post
        action: Review action (approve, reject, edit)
        feedback: Human feedback text
        reviewed_at: When the review occurred
    """
    
    __tablename__ = "reviews"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="reviews")


class Evaluation(Base):
    """Evaluation metrics for generated content.
    
    Attributes:
        id: Primary key
        post_id: Foreign key to Post
        metric_name: Name of the metric (readability, grammar, relevance, etc.)
        score: Numeric score for the metric
        evaluator_type: Type of evaluator (quality, platform, llm_judge)
        metadata: Additional evaluation metadata (JSON)
        created_at: When the evaluation was performed
    """
    
    __tablename__ = "evaluations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    evaluator_type: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    # Relationships
    post: Mapped["Post"] = relationship("Post", back_populates="evaluations")

