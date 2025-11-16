"""Pydantic schemas for post content across different platforms.

This module defines the structure for platform-specific content,
including images, text, and metadata.
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ImageData(BaseModel):
    """Image information for a post.
    
    Attributes:
        url: URL or path to the image
        prompt: The prompt used to generate the image
        alt_text: Alternative text for accessibility
    """
    
    url: str
    prompt: str
    alt_text: Optional[str] = None


class LinkedInPost(BaseModel):
    """LinkedIn post content.
    
    LinkedIn posts are professional and concise (max 3000 characters).
    The image is typically displayed at the top of the post.
    
    Attributes:
        text: Main post content
        image: Optional image for the post
        hashtags: List of relevant hashtags
        character_count: Total character count
    """
    
    text: str = Field(..., max_length=3000)
    image: Optional[ImageData] = None
    hashtags: List[str] = Field(default_factory=list, max_items=5)
    
    @property
    def character_count(self) -> int:
        """Calculate character count."""
        return len(self.text)


class InstagramPost(BaseModel):
    """Instagram post content.
    
    Instagram is visual-first with engaging captions and hashtags.
    The image is the primary focus.
    
    Attributes:
        caption: Post caption (max 2200 characters)
        image: Required image for the post
        hashtags: List of hashtags (recommended 10-30)
        alt_text: Image description for accessibility
    """
    
    caption: str = Field(..., max_length=2200)
    image: ImageData
    hashtags: List[str] = Field(default_factory=list, min_items=10, max_items=30)
    alt_text: Optional[str] = None


class WordPressSection(BaseModel):
    """A section of a WordPress post.
    
    WordPress posts are structured with headers, paragraphs, and images.
    Images can be placed anywhere within the content.
    
    Attributes:
        type: Section type (heading, paragraph, image)
        content: Section content (text, image data, etc.)
        level: Heading level (1-6) for heading types
    """
    
    type: str = Field(..., description="Section type: heading, paragraph, image")
    content: str | ImageData
    level: Optional[int] = Field(None, ge=1, le=6, description="Heading level for headings")


class WordPressPost(BaseModel):
    """WordPress article content.
    
    WordPress posts are long-form articles with structured content.
    Images can be embedded throughout the article.
    
    Attributes:
        title: Article title
        excerpt: Short excerpt/summary
        sections: List of content sections (headers, paragraphs, images)
        featured_image: Primary image for the post
        seo_description: Meta description for SEO
        tags: List of tags/categories
    """
    
    title: str = Field(..., max_length=200)
    excerpt: str = Field(..., max_length=500)
    sections: List[WordPressSection] = Field(default_factory=list)
    featured_image: Optional[ImageData] = None
    seo_description: str = Field(..., max_length=160)
    tags: List[str] = Field(default_factory=list, max_items=10)
    
    def to_html(self) -> str:
        """Convert sections to HTML.
        
        Returns:
            HTML representation of the article
        """
        # TODO: Implement HTML conversion
        pass
    
    def insert_image_at_position(self, image: ImageData, position: int) -> None:
        """Insert an image at a specific position in the article.
        
        Args:
            image: Image to insert
            position: Position index in sections list
        """
        image_section = WordPressSection(
            type="image",
            content=image,
        )
        self.sections.insert(position, image_section)


class PostContent(BaseModel):
    """Complete post content for all platforms.
    
    This is the main structure that contains all generated content
    for a single topic across all platforms.
    
    Attributes:
        topic: The original topic
        linkedin: LinkedIn post
        instagram: Instagram post
        wordpress: WordPress article
        shared_image: The main image used across platforms
    """
    
    topic: str
    linkedin: Optional[LinkedInPost] = None
    instagram: Optional[InstagramPost] = None
    wordpress: Optional[WordPressPost] = None
    shared_image: Optional[ImageData] = None

