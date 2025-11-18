"""Tests for agent workflow control nodes.

This module tests the workflow control nodes (wait_for_approval, apply_feedback,
finalize, handle_error) and content generation nodes following TDD principles.
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.agent.llm_schemas import (
    InstagramContentOutput,
    LinkedInContentOutput,
    TopicAnalysisOutput,
    WordPressContentOutput,
    WordPressSectionOutput,
)
from src.agent.nodes import (
    analyze_topic,
    apply_feedback,
    finalize,
    generate_instagram,
    generate_linkedin,
    generate_wordpress,
    handle_error,
    wait_for_approval,
)
from src.agent.schemas import ImageData, InstagramPost, LinkedInPost, WordPressPost
from src.agent.state import PostGenerationState
from src.db.models import Base

# ===== Test Database Setup =====


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test.

    Yields:
        SQLAlchemy Session
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ===== Test wait_for_approval Node =====


class TestWaitForApproval:
    """Tests for wait_for_approval node."""

    def test_sets_approval_status_to_pending_review(self):
        """Test that wait_for_approval sets approval_status to pending_review."""
        # Arrange
        state = PostGenerationState(
            topic="Test topic",
            post_id=1,
            approval_status="pending_generation",
        )

        # Act
        result = wait_for_approval(state)

        # Assert
        assert result["approval_status"] == "pending_review"

    def test_preserves_post_id(self):
        """Test that wait_for_approval preserves post_id."""
        # Arrange
        state = PostGenerationState(
            topic="Test topic",
            post_id=42,
        )

        # Act
        result = wait_for_approval(state)

        # Assert - Should only return approval_status, not modify post_id
        assert "approval_status" in result
        assert "post_id" not in result  # Shouldn't override existing fields


# ===== Test apply_feedback Node =====


class TestApplyFeedback:
    """Tests for apply_feedback node."""

    def test_regenerate_all_platforms_when_no_specific_platform_mentioned(self):
        """Test that all platforms are regenerated when feedback doesn't mention specific platform."""
        # Arrange
        state = PostGenerationState(
            topic="Test topic",
            post_id=1,
            feedback="Please make the content more engaging and professional",
            approval_status="rejected",
        )

        # Act
        result = apply_feedback(state)

        # Assert
        assert result["regenerate_linkedin"] is True
        assert result["regenerate_instagram"] is True
        assert result["regenerate_wordpress"] is True
        assert result["approval_status"] == "regenerating"

    def test_regenerate_only_linkedin_when_mentioned(self):
        """Test that only LinkedIn is regenerated when mentioned in feedback."""
        # Arrange
        state = PostGenerationState(
            topic="Test topic",
            post_id=1,
            feedback="The LinkedIn post needs to be more professional",
            approval_status="rejected",
        )

        # Act
        result = apply_feedback(state)

        # Assert
        assert result["regenerate_linkedin"] is True
        assert result["regenerate_instagram"] is False
        assert result["regenerate_wordpress"] is False

    def test_regenerate_only_instagram_when_mentioned(self):
        """Test that only Instagram is regenerated when mentioned in feedback."""
        # Arrange
        state = PostGenerationState(
            topic="Test topic",
            post_id=1,
            feedback="The instagram caption needs more hashtags",
            approval_status="rejected",
        )

        # Act
        result = apply_feedback(state)

        # Assert
        assert result["regenerate_linkedin"] is False
        assert result["regenerate_instagram"] is True
        assert result["regenerate_wordpress"] is False

    def test_regenerate_only_wordpress_when_mentioned(self):
        """Test that only WordPress is regenerated when mentioned in feedback."""
        # Arrange
        state = PostGenerationState(
            topic="Test topic",
            post_id=1,
            feedback="The wordpress article is too short",
            approval_status="rejected",
        )

        # Act
        result = apply_feedback(state)

        # Assert
        assert result["regenerate_linkedin"] is False
        assert result["regenerate_instagram"] is False
        assert result["regenerate_wordpress"] is True

    def test_regenerate_multiple_platforms_when_mentioned(self):
        """Test that multiple platforms are regenerated when mentioned in feedback."""
        # Arrange
        state = PostGenerationState(
            topic="Test topic",
            post_id=1,
            feedback="Both the LinkedIn and Instagram posts need improvement",
            approval_status="rejected",
        )

        # Act
        result = apply_feedback(state)

        # Assert
        assert result["regenerate_linkedin"] is True
        assert result["regenerate_instagram"] is True
        assert result["regenerate_wordpress"] is False


# ===== Test finalize Node =====


class TestFinalize:
    """Tests for finalize node."""

    def test_sets_approval_status_to_approved(self):
        """Test that finalize sets approval_status to approved."""
        # Arrange
        state = PostGenerationState(
            topic="Test topic",
            post_id=1,
            approval_status="pending_review",
        )

        # Act
        result = finalize(state)

        # Assert
        assert result["approval_status"] == "approved"
        assert result["finalized"] is True

    def test_finalize_logs_post_id(self, caplog):
        """Test that finalize logs the post ID."""
        # Arrange
        state = PostGenerationState(
            topic="Test topic",
            post_id=123,
        )

        # Act
        with caplog.at_level("INFO"):
            _ = finalize(state)

        # Assert
        assert "post 123" in caplog.text.lower() or "123" in caplog.text


# ===== Test handle_error Node =====


class TestHandleError:
    """Tests for handle_error node."""

    def test_sets_approval_status_to_error(self):
        """Test that handle_error sets approval_status to error."""
        # Arrange
        state = PostGenerationState(
            topic="Test topic",
            post_id=1,
            error="Something went wrong",
            approval_status="pending_generation",
        )

        # Act
        result = handle_error(state)

        # Assert
        assert result["approval_status"] == "error"
        assert result["finalized"] is False

    def test_logs_error_message(self, caplog):
        """Test that handle_error logs the error message."""
        # Arrange
        error_message = "Failed to generate content"
        state = PostGenerationState(
            topic="Test topic",
            post_id=1,
            error=error_message,
        )

        # Act
        with caplog.at_level("ERROR"):
            _ = handle_error(state)

        # Assert
        assert error_message in caplog.text

    def test_preserves_error_message(self):
        """Test that handle_error preserves the error message."""
        # Arrange
        error_message = "API rate limit exceeded"
        state = PostGenerationState(
            topic="Test topic",
            post_id=1,
            error=error_message,
        )

        # Act
        result = handle_error(state)

        # Assert - Error should remain in state (not overridden)
        assert "error" not in result or result.get("error") is None


# ===== Test Content Generation Nodes =====


class TestAnalyzeTopic:
    """Test suite for analyze_topic node."""

    @patch("src.agent.nodes.LLMRouter")
    def test_analyze_topic_success(self, mock_router_class):
        """Test successful topic analysis with Pydantic structured output."""
        # Mock LLM response as Pydantic model
        mock_analysis = TopicAnalysisOutput(
            themes=["AI", "Machine Learning", "Innovation"],
            audience="Tech professionals and business leaders",
            visual_concepts=[
                "Futuristic AI brain",
                "Connected network nodes",
                "Digital transformation",
            ],
            tone="professional",
            takeaways=[
                "AI is transforming business",
                "Practical applications exist today",
            ],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_analysis
        mock_router_class.return_value = mock_router

        # Create initial state
        state = PostGenerationState(topic="The future of AI in business", post_id=1)

        # Call node
        result = analyze_topic(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()
        call_args = mock_router.generate_structured.call_args
        assert call_args[1]["response_model"] == TopicAnalysisOutput
        assert "The future of AI in business" in call_args[1]["prompt"]

        # Verify result
        assert "analysis" in result
        assert "themes" in result
        assert "target_audience" in result
        assert "visual_concepts" in result

        assert result["themes"] == ["AI", "Machine Learning", "Innovation"]
        assert result["target_audience"] == "Tech professionals and business leaders"
        assert len(result["visual_concepts"]) == 3

    @patch("src.agent.nodes.LLMRouter")
    def test_analyze_topic_extracts_all_fields(self, mock_router_class):
        """Test that all required fields are extracted."""
        mock_analysis = TopicAnalysisOutput(
            themes=["Topic A", "Topic B", "Topic C"],
            audience="General audience",
            visual_concepts=["Concept 1", "Concept 2", "Concept 3"],
            tone="casual",
            takeaways=["Key point", "Another point"],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_analysis
        mock_router_class.return_value = mock_router

        state = PostGenerationState(topic="Test topic", post_id=1)
        result = analyze_topic(state)

        # All fields should be present
        assert isinstance(result["analysis"], dict)
        assert isinstance(result["themes"], list)
        assert isinstance(result["target_audience"], str)
        assert isinstance(result["visual_concepts"], list)


class TestGenerateLinkedIn:
    """Test suite for generate_linkedin node."""

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_linkedin_success(self, mock_router_class):
        """Test successful LinkedIn post generation."""
        mock_content = LinkedInContentOutput(
            text="AI is transforming the way we work. Here are 3 key insights...",
            hashtags=["AI", "Innovation", "Business"],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        # Create state with image
        image = ImageData(
            url="https://example.com/image.png",
            prompt="AI brain illustration",
            alt_text="AI concept",
        )
        state = PostGenerationState(
            topic="AI in business",
            post_id=1,
            themes=["AI", "Innovation"],
            target_audience="Business leaders",
            image=image,
        )

        result = generate_linkedin(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Verify result structure
        assert "linkedin_post" in result
        linkedin_post = result["linkedin_post"]

        assert "text" in linkedin_post
        assert "hashtags" in linkedin_post
        assert "image" in linkedin_post

        # Verify content
        assert len(linkedin_post["text"]) > 0
        assert isinstance(linkedin_post["hashtags"], list)
        assert len(linkedin_post["hashtags"]) <= 5

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_linkedin_character_limit(self, mock_router_class):
        """Test LinkedIn post respects 3000 character limit."""
        # Create a post that's exactly at the limit
        long_text = "A" * 3000
        mock_content = LinkedInContentOutput(text=long_text, hashtags=["AI", "Tech"])

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=ImageData(url="test.png", prompt="test"),
        )

        result = generate_linkedin(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Should validate successfully at 3000 chars
        linkedin_post = LinkedInPost(**result["linkedin_post"])
        assert linkedin_post.character_count <= 3000

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_linkedin_hashtag_limit(self, mock_router_class):
        """Test LinkedIn post respects max 5 hashtags."""
        mock_content = LinkedInContentOutput(
            text="Test post",
            hashtags=["AI", "ML", "Tech"],  # Only 3 hashtags
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=ImageData(url="test.png", prompt="test"),
        )

        result = generate_linkedin(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Validate with Pydantic
        linkedin_post = LinkedInPost(**result["linkedin_post"])
        assert len(linkedin_post.hashtags) <= 5

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_linkedin_includes_image(self, mock_router_class):
        """Test LinkedIn post includes image reference."""
        mock_content = LinkedInContentOutput(text="Test post with image", hashtags=["AI", "Tech"])

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="https://example.com/ai.png", prompt="AI illustration")
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_linkedin(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Image should be included in post
        assert result["linkedin_post"]["image"] is not None
        assert result["linkedin_post"]["image"]["url"] == image.url


class TestGenerateInstagram:
    """Test suite for generate_instagram node."""

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_instagram_success(self, mock_router_class):
        """Test successful Instagram post generation."""
        mock_content = InstagramContentOutput(
            caption="Transform your business with AI! 🚀 Check out these insights...",
            hashtags=[
                "AI",
                "MachineLearning",
                "Tech",
                "Innovation",
                "Business",
                "Future",
                "Technology",
                "Digital",
                "Automation",
                "Data",
            ],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="https://example.com/image.png", prompt="AI brain")
        state = PostGenerationState(
            topic="AI in business",
            post_id=1,
            themes=["AI", "Innovation"],
            target_audience="Young professionals",
            image=image,
        )

        result = generate_instagram(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Verify result
        assert "instagram_post" in result
        instagram_post = result["instagram_post"]

        assert "caption" in instagram_post
        assert "hashtags" in instagram_post
        assert "image" in instagram_post

        # Verify hashtag count (10-30)
        assert 10 <= len(instagram_post["hashtags"]) <= 30

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_instagram_character_limit(self, mock_router_class):
        """Test Instagram caption respects 2200 character limit."""
        caption = "A" * 2200
        mock_content = InstagramContentOutput(
            caption=caption,
            hashtags=["AI"] * 15,  # 15 hashtags
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="test.png", prompt="test")
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_instagram(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Should validate successfully
        instagram_post = InstagramPost(**result["instagram_post"])
        assert len(instagram_post.caption) <= 2200

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_instagram_hashtag_count(self, mock_router_class):
        """Test Instagram post has 10-30 hashtags."""
        hashtags = [f"Tag{i}" for i in range(20)]  # 20 hashtags
        mock_content = InstagramContentOutput(caption="Test caption", hashtags=hashtags)

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="test.png", prompt="test")
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_instagram(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Validate with Pydantic
        instagram_post = InstagramPost(**result["instagram_post"])
        assert 10 <= len(instagram_post.hashtags) <= 30

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_instagram_requires_image(self, mock_router_class):
        """Test Instagram post requires an image."""
        mock_content = InstagramContentOutput(
            caption="Test caption",
            hashtags=[f"Tag{i}" for i in range(15)],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="https://example.com/image.png", prompt="Test image")
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_instagram(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Image is required for Instagram
        instagram_post = InstagramPost(**result["instagram_post"])
        assert instagram_post.image is not None
        assert instagram_post.image.url == image.url


class TestGenerateWordPress:
    """Test suite for generate_wordpress node."""

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_wordpress_success(self, mock_router_class):
        """Test successful WordPress article generation."""
        mock_content = WordPressContentOutput(
            title="AI in Business: A Complete Guide for Modern Leaders",
            excerpt="Discover how AI is transforming business operations.",
            seo_description="Discover how artificial intelligence is transforming modern business operations and learn what it means for your company's future success today and beyond.",
            sections=[
                WordPressSectionOutput(type="paragraph", content="Introduction paragraph..."),
                WordPressSectionOutput(type="heading", content="What is AI?", level=2),
                WordPressSectionOutput(type="paragraph", content="AI explanation..."),
                WordPressSectionOutput(type="image", content="image_reference"),
                WordPressSectionOutput(type="heading", content="Benefits of AI", level=2),
                WordPressSectionOutput(type="paragraph", content="Benefits discussion..."),
            ],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="https://example.com/ai.png", prompt="AI illustration")
        state = PostGenerationState(
            topic="AI in business",
            post_id=1,
            themes=["AI", "Innovation"],
            target_audience="Business leaders",
            image=image,
        )

        result = generate_wordpress(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Verify result
        assert "wordpress_post" in result
        wordpress_post = result["wordpress_post"]

        assert "title" in wordpress_post
        assert "seo_description" in wordpress_post
        assert "sections" in wordpress_post
        assert "featured_image" in wordpress_post

        # Verify structure
        assert len(wordpress_post["sections"]) > 0

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_wordpress_section_structure(self, mock_router_class):
        """Test WordPress sections have correct structure."""
        mock_content = WordPressContentOutput(
            title="Understanding Modern AI: A Complete Business Guide",
            excerpt="Test excerpt",
            seo_description="Learn about modern artificial intelligence and how it impacts business operations with practical insights and actionable strategies for your future success.",
            sections=[
                WordPressSectionOutput(type="heading", content="Introduction", level=2),
                WordPressSectionOutput(type="paragraph", content="Intro text"),
                WordPressSectionOutput(type="image", content="image_reference"),
                WordPressSectionOutput(type="heading", content="Conclusion", level=2),
                WordPressSectionOutput(type="paragraph", content="Conclusion text"),
            ],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="test.png", prompt="test")
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_wordpress(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Validate with Pydantic
        wordpress_post = WordPressPost(**result["wordpress_post"])

        # Check sections
        assert len(wordpress_post.sections) == 5
        assert wordpress_post.sections[0].type == "heading"
        assert wordpress_post.sections[0].level == 2
        assert wordpress_post.sections[2].type == "image"

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_wordpress_title_length(self, mock_router_class):
        """Test WordPress title respects max 200 characters."""
        mock_content = WordPressContentOutput(
            title="Testing WordPress Article Title Length Constraints Here",
            excerpt="Test excerpt",
            seo_description="This is a longer SEO description that meets the minimum character requirement of 150 characters for proper search engine optimization and full validation.",
            sections=[
                WordPressSectionOutput(type="heading", content="Introduction", level=2),
                WordPressSectionOutput(type="paragraph", content="Content paragraph 1"),
                WordPressSectionOutput(type="paragraph", content="Content paragraph 2"),
                WordPressSectionOutput(type="heading", content="Conclusion", level=2),
                WordPressSectionOutput(type="paragraph", content="Content paragraph 3"),
            ],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="test.png", prompt="test")
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_wordpress(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        wordpress_post = WordPressPost(**result["wordpress_post"])
        assert len(wordpress_post.title) <= 200

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_wordpress_seo_description_length(self, mock_router_class):
        """Test WordPress SEO description respects max 160 characters."""
        mock_content = WordPressContentOutput(
            title="WordPress SEO Description Testing with Character Limit",
            excerpt="Test excerpt",
            seo_description="A" * 160,  # Exactly 160 chars
            sections=[
                WordPressSectionOutput(type="heading", content="Introduction", level=2),
                WordPressSectionOutput(type="paragraph", content="Content paragraph 1"),
                WordPressSectionOutput(type="paragraph", content="Content paragraph 2"),
                WordPressSectionOutput(type="heading", content="Conclusion", level=2),
                WordPressSectionOutput(type="paragraph", content="Content paragraph 3"),
            ],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="test.png", prompt="test")
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_wordpress(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        wordpress_post = WordPressPost(**result["wordpress_post"])
        assert len(wordpress_post.seo_description) <= 160

    @patch("src.agent.nodes.LLMRouter")
    def test_generate_wordpress_includes_image(self, mock_router_class):
        """Test WordPress article includes image in sections."""
        mock_content = WordPressContentOutput(
            title="WordPress Article with Images: A Complete Testing Guide",
            excerpt="Test excerpt",
            seo_description="Learn how WordPress articles can include images in their sections with this complete guide covering all the essential aspects and best practices for success.",
            sections=[
                WordPressSectionOutput(type="paragraph", content="Intro"),
                WordPressSectionOutput(type="image", content="image_reference"),
                WordPressSectionOutput(type="paragraph", content="Body paragraph 1"),
                WordPressSectionOutput(type="heading", content="Conclusion", level=2),
                WordPressSectionOutput(type="paragraph", content="Body paragraph 2"),
            ],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(
            url="https://example.com/image.png",
            prompt="Test image",
            alt_text="Test alt",
        )
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_wordpress(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        wordpress_post = WordPressPost(**result["wordpress_post"])

        # Find image section
        image_sections = [s for s in wordpress_post.sections if s.type == "image"]
        assert len(image_sections) > 0

        # Image should be the actual ImageData object
        image_section = image_sections[0]
        assert isinstance(image_section.content, ImageData)
        assert image_section.content.url == image.url


class TestPydanticValidation:
    """Test that all generated content validates against Pydantic models."""

    @patch("src.agent.nodes.LLMRouter")
    def test_linkedin_pydantic_validation(self, mock_router_class):
        """Test LinkedIn content validates with Pydantic."""
        mock_content = LinkedInContentOutput(
            text="Valid LinkedIn post",
            hashtags=["AI", "Tech"],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="test.png", prompt="test")
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_linkedin(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Should not raise validation error
        linkedin_post = LinkedInPost(**result["linkedin_post"])
        assert linkedin_post.text == "Valid LinkedIn post"

    @patch("src.agent.nodes.LLMRouter")
    def test_instagram_pydantic_validation(self, mock_router_class):
        """Test Instagram content validates with Pydantic."""
        mock_content = InstagramContentOutput(
            caption="Valid Instagram caption",
            hashtags=[f"Tag{i}" for i in range(15)],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="test.png", prompt="test")
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_instagram(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Should not raise validation error
        instagram_post = InstagramPost(**result["instagram_post"])
        assert instagram_post.caption == "Valid Instagram caption"

    @patch("src.agent.nodes.LLMRouter")
    def test_wordpress_pydantic_validation(self, mock_router_class):
        """Test WordPress content validates with Pydantic."""
        mock_content = WordPressContentOutput(
            title="Valid WordPress Title: A Complete Pydantic Test Guide",
            excerpt="Valid excerpt",
            seo_description="This is a valid SEO description that meets the minimum character requirement of 150 characters for proper validation and search engine optimization success.",
            sections=[
                WordPressSectionOutput(type="heading", content="Introduction", level=2),
                WordPressSectionOutput(type="paragraph", content="Paragraph 1"),
                WordPressSectionOutput(type="paragraph", content="Paragraph 2"),
                WordPressSectionOutput(type="heading", content="Conclusion", level=2),
                WordPressSectionOutput(type="paragraph", content="Paragraph 3"),
            ],
        )

        mock_router = MagicMock()
        mock_router.generate_structured.return_value = mock_content
        mock_router_class.return_value = mock_router

        image = ImageData(url="test.png", prompt="test")
        state = PostGenerationState(
            topic="Test",
            post_id=1,
            themes=["Test"],
            target_audience="Everyone",
            image=image,
        )

        result = generate_wordpress(state)

        # Verify LLM was called with generate_structured
        mock_router.generate_structured.assert_called_once()

        # Should not raise validation error
        wordpress_post = WordPressPost(**result["wordpress_post"])
        assert wordpress_post.title == "Valid WordPress Title: A Complete Pydantic Test Guide"
