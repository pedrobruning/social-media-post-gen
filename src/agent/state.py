"""LangGraph state schema for post generation workflow.

This module defines the state structure that flows through the LangGraph agent.
The state tracks all information needed for generating and reviewing posts.
"""

from pydantic import BaseModel, Field

from src.agent.schemas import ImageData, InstagramPost, LinkedInPost, WordPressPost


class PostGenerationState(BaseModel):
    """State schema for the post generation agent workflow.

    This state is passed between all nodes in the LangGraph agent.
    Each node can read from and write to this state using Pydantic models.

    Attributes:
        topic: The original topic provided by the user
        post_id: Database ID of the post record

        # Topic analysis
        analysis: Full topic analysis from LLM (JSON dict)
        themes: Key themes/concepts extracted from topic
        target_audience: Target audience description
        visual_concepts: Visual concepts for image generation

        # Image generation
        image: Generated image data with URL and prompt

        # Platform-specific content (Pydantic models)
        linkedin_post: Generated LinkedIn post
        instagram_post: Generated Instagram post
        wordpress_post: Generated WordPress article

        # Human-in-the-loop review
        approval_status: Status of human review (pending_generation/pending_review/approved/rejected/regenerating)
        feedback: Human feedback for regeneration
        regenerate_linkedin: Whether to regenerate LinkedIn post
        regenerate_instagram: Whether to regenerate Instagram post
        regenerate_wordpress: Whether to regenerate WordPress article

        # Finalization
        finalized: Whether the workflow has been finalized

        # Error handling
        error: Any error that occurred during processing
        retry_count: Number of retries attempted
    """

    # Core information
    topic: str
    post_id: int

    # Topic analysis
    analysis: dict | None = None  # Full topic analysis from LLM
    themes: list[str] = Field(default_factory=list)  # Key themes extracted
    target_audience: str | None = None  # Target audience description
    visual_concepts: list[str] = Field(default_factory=list)  # Visual concepts for image

    # Image generation
    image: ImageData | None = None

    # Platform-specific content (using Pydantic models)
    linkedin_post: LinkedInPost | None = None
    instagram_post: InstagramPost | None = None
    wordpress_post: WordPressPost | None = None

    # Human review
    approval_status: str = Field(
        default="pending_generation",
        description="Status: pending_generation, pending_review, approved, rejected, regenerating",
    )
    feedback: str | None = None

    # Regeneration flags (set by apply_feedback node)
    regenerate_linkedin: bool = False
    regenerate_instagram: bool = False
    regenerate_wordpress: bool = False

    # Finalization
    finalized: bool = False

    # Error handling
    error: str | None = None
    retry_count: int = 0

    class Config:
        """Pydantic config for state model."""

        arbitrary_types_allowed = True
