"""Pydantic models for LLM structured outputs.

This module defines Pydantic models that LLMs use to return structured data.
Using Pydantic with LLM calls ensures type safety and validation.
"""

from pydantic import BaseModel, Field


class TopicAnalysisOutput(BaseModel):
    """Structured output for topic analysis.

    This model ensures the LLM returns properly formatted topic analysis
    with all required fields validated.
    """

    themes: list[str] = Field(
        description="3-5 key themes or concepts from the topic",
        min_length=3,
        max_length=5,
    )
    audience: str = Field(description="Target audience description")
    visual_concepts: list[str] = Field(
        description="3 visual concepts for image generation",
        min_length=3,
        max_length=3,
    )
    tone: str = Field(
        description="Recommended content tone (professional/casual/inspirational/educational)"
    )
    takeaways: list[str] = Field(
        description="Key takeaways to communicate",
        min_length=2,
        max_length=5,
    )


class LinkedInContentOutput(BaseModel):
    """Structured output for LinkedIn post generation.

    Ensures the LLM returns properly formatted LinkedIn content
    with character and hashtag limits enforced.
    """

    text: str = Field(
        description="LinkedIn post text (max 3000 characters)",
        max_length=3000,
    )
    hashtags: list[str] = Field(
        description="2-5 relevant hashtags",
        min_length=2,
        max_length=5,
    )


class InstagramContentOutput(BaseModel):
    """Structured output for Instagram post generation.

    Ensures the LLM returns properly formatted Instagram content
    with character and hashtag requirements enforced.
    """

    caption: str = Field(
        description="Instagram caption (max 2200 characters)",
        max_length=2200,
    )
    hashtags: list[str] = Field(
        description="10-30 relevant hashtags",
        min_length=10,
        max_length=30,
    )


class WordPressSectionOutput(BaseModel):
    """Individual section in WordPress article."""

    type: str = Field(
        description="Section type: heading, paragraph, or image",
        pattern="^(heading|paragraph|image)$",
    )
    content: str = Field(description="Section content (or 'image_reference' for images)")
    level: int | None = Field(
        default=None,
        description="Heading level (2-4) for heading sections only",
        ge=2,
        le=4,
    )


class WordPressContentOutput(BaseModel):
    """Structured output for WordPress article generation.

    Ensures the LLM returns properly formatted WordPress article
    with all SEO and structural requirements.
    """

    title: str = Field(
        description="Article title (50-60 characters)",
        min_length=50,
        max_length=60,
    )
    excerpt: str = Field(
        description="Brief excerpt (max 500 characters)",
        max_length=500,
    )
    seo_description: str = Field(
        description="SEO meta description (150-160 characters)",
        min_length=150,
        max_length=160,
    )
    sections: list[WordPressSectionOutput] = Field(
        description="Article sections (introduction, body, conclusion)",
        min_length=5,
    )
