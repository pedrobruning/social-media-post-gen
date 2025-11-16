"""LangGraph state schema for post generation workflow.

This module defines the state structure that flows through the LangGraph agent.
The state tracks all information needed for generating and reviewing posts.
"""

from typing import Optional, TypedDict


class PostGenerationState(TypedDict):
    """State schema for the post generation agent workflow.
    
    This state is passed between all nodes in the LangGraph agent.
    Each node can read from and write to this state.
    
    Attributes:
        topic: The original topic provided by the user
        post_id: Database ID of the post record
        
        # Image generation
        image_url: URL/path to the generated image
        image_prompt: The prompt used to generate the image
        
        # Platform-specific content
        linkedin_post: Generated LinkedIn post content
        instagram_post: Generated Instagram post content
        wordpress_post: Generated WordPress article content
        
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
    image_url: Optional[str]
    image_prompt: Optional[str]
    
    # Platform-specific content (dict with text, metadata)
    linkedin_post: Optional[dict]
    instagram_post: Optional[dict]
    wordpress_post: Optional[dict]
    
    # Human review
    approval_status: str  # pending_review, approved, rejected
    feedback: Optional[str]
    
    # Error handling
    error: Optional[str]
    retry_count: int

