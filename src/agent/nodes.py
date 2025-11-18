"""LangGraph agent nodes for post generation workflow.

This module defines all the nodes (functions) that make up the agent workflow.
Each node performs a specific task in the content generation pipeline.
"""

import json
import logging

from src.agent.schemas import (
    InstagramPost,
    LinkedInPost,
    WordPressPost,
    WordPressSection,
)
from src.agent.state import PostGenerationState
from src.llm.router import LLMRouter

logger = logging.getLogger(__name__)


def analyze_topic(state: PostGenerationState) -> dict:
    """Analyze the topic to extract themes, audience, and visual concepts.

    This is the first node in the workflow. It analyzes the user's topic
    to understand what content needs to be generated.

    Args:
        state: Current agent state

    Returns:
        Dict with updated state fields
    """
    logger.info(f"Analyzing topic: {state.topic}")

    system_prompt = """You are a content strategist analyzing topics for social media.
Extract key information to guide content generation."""

    prompt = f"""Analyze this topic: "{state.topic}"

Provide:
1. 3-5 key themes/concepts
2. Target audience description
3. 3 visual concepts for an image
4. Content tone (professional/casual/inspirational)
5. Key takeaways to communicate

Return as JSON with keys: themes, audience, visual_concepts, tone, takeaways"""

    # Call LLM
    llm_router = LLMRouter()
    response = llm_router.generate(prompt, system_prompt)

    # Parse JSON response
    analysis = json.loads(response)

    logger.info(f"Extracted {len(analysis.get('themes', []))} themes for topic")

    return {
        "analysis": analysis,
        "themes": analysis["themes"],
        "target_audience": analysis["audience"],
        "visual_concepts": analysis["visual_concepts"],
    }


def generate_image(state: PostGenerationState) -> dict:
    """Generate an image for the post using DALL-E 3.

    Creates a visual asset that can be reused across all platforms.

    Args:
        state: Current agent state

    Returns:
        Dict with image_url and image_prompt fields
    """
    # TODO: Implement image generation
    # 1. Generate optimized DALL-E prompt from topic analysis
    # 2. Call DALL-E API via OpenRouter
    # 3. Download and store image
    # 4. Update state with image_url
    pass


def generate_linkedin(state: PostGenerationState) -> dict:
    """Generate LinkedIn post content.

    Creates a professional post optimized for LinkedIn (max 3000 chars).

    Args:
        state: Current agent state

    Returns:
        Dict with linkedin_post field
    """
    logger.info(f"Generating LinkedIn post for topic: {state.topic}")

    system_prompt = "You are a LinkedIn content expert creating professional posts."

    # Get image description if available
    image_desc = state.image.prompt if state.image else "N/A"

    prompt = f"""Create a LinkedIn post about: {state.topic}

Context:
- Themes: {', '.join(state.themes) if state.themes else 'N/A'}
- Audience: {state.target_audience or 'General professionals'}
- Image: {image_desc}

Requirements:
1. Start with attention-grabbing hook (first 2 lines)
2. Provide valuable insights
3. Maximum 3000 characters
4. Professional tone
5. Include 2-5 relevant hashtags at the end
6. End with thought-provoking question or CTA
7. Reference the attached image naturally

Return JSON: {{"text": "...", "hashtags": ["...", "..."]}}"""

    # Call LLM
    llm_router = LLMRouter()
    response = llm_router.generate(prompt, system_prompt)

    # Parse JSON response
    content = json.loads(response)

    # Validate with Pydantic
    linkedin_post = LinkedInPost(
        text=content["text"], hashtags=content["hashtags"], image=state.image
    )

    logger.info(
        f"Generated LinkedIn post: {linkedin_post.character_count} chars, "
        f"{len(linkedin_post.hashtags)} hashtags"
    )

    return {"linkedin_post": linkedin_post.model_dump()}


def generate_instagram(state: PostGenerationState) -> dict:
    """Generate Instagram post content.

    Creates a visual-focused caption with hashtags.

    Args:
        state: Current agent state

    Returns:
        Dict with instagram_post field
    """
    logger.info(f"Generating Instagram post for topic: {state.topic}")

    system_prompt = (
        "You are an Instagram content creator. Create engaging, visual-focused captions."
    )

    # Get image description
    image_desc = state.image.prompt if state.image else "N/A"

    prompt = f"""Create an Instagram caption about: {state.topic}

Context:
- Themes: {', '.join(state.themes) if state.themes else 'N/A'}
- Audience: {state.target_audience or 'General audience'}
- Image shows: {image_desc}

Requirements:
1. Start with attention-grabbing first line
2. Tell a story that connects to the image
3. Use 2-3 relevant emojis naturally
4. Maximum 2200 characters
5. Include 10-30 relevant hashtags
6. Conversational, authentic tone
7. End with engagement question

Return JSON: {{"caption": "...", "hashtags": ["...", ...]}}"""

    # Call LLM
    llm_router = LLMRouter()
    response = llm_router.generate(prompt, system_prompt)

    # Parse JSON response
    content = json.loads(response)

    # Validate with Pydantic
    instagram_post = InstagramPost(
        caption=content["caption"], hashtags=content["hashtags"], image=state.image
    )

    logger.info(
        f"Generated Instagram post: {len(instagram_post.caption)} chars, "
        f"{len(instagram_post.hashtags)} hashtags"
    )

    return {"instagram_post": instagram_post.model_dump()}


def generate_wordpress(state: PostGenerationState) -> dict:
    """Generate WordPress article content.

    Creates a long-form article with proper structure and SEO.

    Args:
        state: Current agent state

    Returns:
        Dict with wordpress_post field
    """
    logger.info(f"Generating WordPress article for topic: {state.topic}")

    system_prompt = "You are a WordPress content writer creating structured articles."

    # Get image description
    image_desc = state.image.prompt if state.image else "N/A"

    prompt = f"""Create an article about: {state.topic}

Context:
- Themes: {', '.join(state.themes) if state.themes else 'N/A'}
- Audience: {state.target_audience or 'General readers'}
- Available image: {image_desc}

Requirements:
1. Compelling title (50-60 chars)
2. SEO meta description (150-160 chars)
3. Brief excerpt (max 500 chars)
4. Structure:
   - Introduction (2-3 paragraphs)
   - 3-5 main sections with H2 headings
   - Conclusion with CTA
   - Place image after intro or in key section
5. 800-1500 words total
6. Professional, informative tone
7. Include examples where relevant

Return JSON:
{{
  "title": "...",
  "excerpt": "...",
  "seo_description": "...",
  "sections": [
    {{"type": "heading", "content": "...", "level": 2}},
    {{"type": "paragraph", "content": "..."}},
    {{"type": "image", "content": "image_reference"}},
    ...
  ]
}}"""

    # Call LLM
    llm_router = LLMRouter()
    response = llm_router.generate(prompt, system_prompt)

    # Parse JSON response
    content = json.loads(response)

    # Build sections with proper types
    sections = []
    for section in content["sections"]:
        if section["type"] == "image":
            # Replace image_reference with actual ImageData
            section["content"] = state.image
        sections.append(WordPressSection(**section))

    # Validate with Pydantic
    wordpress_post = WordPressPost(
        title=content["title"],
        excerpt=content.get("excerpt", ""),
        sections=sections,
        featured_image=state.image,
        seo_description=content["seo_description"],
    )

    logger.info(
        f"Generated WordPress article: {len(wordpress_post.sections)} sections, "
        f"title: {wordpress_post.title[:50]}..."
    )

    return {"wordpress_post": wordpress_post.model_dump()}


def wait_for_approval(state: PostGenerationState) -> dict:
    """Wait for human approval of generated content.

    This is the human-in-the-loop checkpoint. The agent pauses here
    until a human reviews and approves or rejects the content.

    Args:
        state: Current agent state

    Returns:
        Dict with approval_status field
    """
    # TODO: Implement checkpoint logic
    # This node marks the state for human review
    # The actual review happens via API endpoints
    return {
        "approval_status": "pending_review",
    }


def apply_feedback(state: PostGenerationState) -> dict:
    """Apply human feedback to regenerate content.

    Uses the feedback from rejection to improve the content.

    Args:
        state: Current agent state (includes feedback)

    Returns:
        Dict with updated state for regeneration
    """
    logger.info(f"Applying feedback for post {state.post_id}: {state.feedback}")

    # Determine which platforms need regeneration based on feedback
    feedback_lower = (state.feedback or "").lower()

    regenerate_flags = {
        "regenerate_linkedin": "linkedin" in feedback_lower,
        "regenerate_instagram": "instagram" in feedback_lower,
        "regenerate_wordpress": "wordpress" in feedback_lower,
    }

    # If no specific platform mentioned, regenerate all
    if not any(regenerate_flags.values()):
        regenerate_flags = dict.fromkeys(regenerate_flags, True)

    return {
        **regenerate_flags,
        "approval_status": "regenerating",
    }


def finalize(state: PostGenerationState) -> dict:
    """Finalize the post after approval.

    Saves all content to the database and marks the post as approved.

    Args:
        state: Current agent state

    Returns:
        Dict with final status
    """
    logger.info(f"Finalizing post {state.post_id}")

    # Note: Database saving is handled by the API layer, not here.
    # This node just marks the workflow as complete.

    return {
        "approval_status": "approved",
        "finalized": True,
    }


def handle_error(state: PostGenerationState) -> dict:
    """Handle errors that occur during generation.

    Args:
        state: Current agent state (includes error)

    Returns:
        Dict with error handling updates
    """
    logger.error(f"Error in post {state.post_id}: {state.error}")

    return {
        "approval_status": "error",
        "finalized": False,
    }
