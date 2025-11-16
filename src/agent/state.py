"""LangGraph state schema for post generation workflow.

This module defines the state structure that flows through the LangGraph agent.
The state tracks all information needed for generating and reviewing posts.
"""

from typing import Optional

from pydantic import BaseModel, Field

from src.agent.schemas import ImageData, InstagramPost, LinkedInPost, WordPressPost


class PostGenerationState(BaseModel):
    """State schema for the post generation agent workflow.
    
    This state is passed between all nodes in the LangGraph agent.
    Each node can read from and write to this state using Pydantic models.
    
    Attributes:
        topic: The original topic provided by the user
        post_id: Database ID of the post record
        
        # Image generation
        image: Generated image data with URL and prompt
        
        # Platform-specific content (Pydantic models)
        linkedin_post: Generated LinkedIn post
        instagram_post: Generated Instagram post
        wordpress_post: Generated WordPress article
        
        # Human-in-the-loop review
        approval_status: Status of human review (pending/approved/rejected)
        feedback: Human feedback for regeneration
        
        # Error handling
        error: Any error that occurred during processing
        retry_count: Number of retries attempted
    """
    
    # Core information
    topic: str
    post_id: int
    
    # Image generation
    image: Optional[ImageData] = None
    
    # Platform-specific content (using Pydantic models)
    linkedin_post: Optional[LinkedInPost] = None
    instagram_post: Optional[InstagramPost] = None
    wordpress_post: Optional[WordPressPost] = None
    
    # Human review
    approval_status: str = Field(
        default="pending_generation",
        description="Status: pending_generation, pending_review, approved, rejected",
    )
    feedback: Optional[str] = None
    
    # Error handling
    error: Optional[str] = None
    retry_count: int = 0
    
    class Config:
        """Pydantic config for state model."""
        
        arbitrary_types_allowed = True

