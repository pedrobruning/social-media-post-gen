"""Tests for image generation using Gemini 2.5 Flash Image.

This module tests the ImageGenerator class for generating images via
Gemini 2.5 Flash Image API through OpenRouter, including prompt generation,
API calls, and base64 image decoding.
"""

import base64
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
from PIL import Image

from src.images.generator import ImageGenerator


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing.

    Yields:
        str: Temporary storage directory path
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_settings(temp_storage):
    """Mock settings with test values.

    This prevents tests from depending on .env file configuration.
    """
    with patch("src.images.generator.settings") as mock_settings:
        mock_settings.image_storage_path = temp_storage
        mock_settings.image_model = "google/gemini-2.5-flash-image-preview:free"
        mock_settings.image_aspect_ratio = "1:1"
        mock_settings.image_format = "png"
        mock_settings.openrouter_api_key = "sk-test-key"
        # Legacy DALL-E settings (kept for backward compatibility)
        mock_settings.image_size = "1024x1024"
        mock_settings.image_quality = "standard"
        mock_settings.image_style = "vivid"
        yield mock_settings


@pytest.fixture
def sample_image_bytes():
    """Create sample image bytes for mocking downloads.

    Returns:
        bytes: PNG image data
    """
    # Create a simple 10x10 blue image
    img = Image.new("RGB", (10, 10), color="blue")

    # Save to bytes
    import io

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


class TestImageGenerator:
    """Test suite for ImageGenerator class."""

    def test_init(self, mock_settings):
        """Test that generator initializes correctly and creates storage directory."""
        generator = ImageGenerator()

        assert generator.storage_path.exists()
        assert generator.storage_path.is_dir()

    def test_generate_prompt_creates_optimized_prompt(self, mock_settings):
        """Test that _generate_prompt creates a DALL-E-optimized prompt from a topic.

        This method should:
        1. Use an LLM to understand the topic
        2. Create a descriptive, visual prompt
        3. Include style guidance for DALL-E

        Example transformation:
        - Input: "AI in healthcare"
        - Output: "A futuristic medical facility with AI diagnostics,
                   professional photography, warm lighting"
        """
        generator = ImageGenerator()
        topic = "The future of artificial intelligence"

        # Mock the LLM call
        with patch("src.images.generator.LLMRouter") as mock_router_class:
            # Setup mock
            mock_router = Mock()
            mock_router.generate.return_value = (
                "A futuristic cityscape with holographic AI interfaces, "
                "vibrant colors, professional digital art, high detail"
            )
            mock_router_class.return_value = mock_router

            # Call the method
            result = generator._generate_prompt(topic)

            # Verify LLM was called
            mock_router.generate.assert_called_once()
            call_args = mock_router.generate.call_args

            # The prompt should contain the topic
            assert topic in str(call_args)

            # Result should be the optimized prompt
            assert result == (
                "A futuristic cityscape with holographic AI interfaces, "
                "vibrant colors, professional digital art, high detail"
            )

    def test_generate_prompt_includes_system_instructions(self, mock_settings):
        """Test that prompt generation includes proper system instructions.

        The system prompt should guide the LLM to:
        - Create visual, descriptive prompts
        - Include style/mood guidance
        - Optimize for DALL-E's capabilities
        """
        generator = ImageGenerator()

        with patch("src.images.generator.LLMRouter") as mock_router_class:
            mock_router = Mock()
            mock_router.generate.return_value = "test prompt"
            mock_router_class.return_value = mock_router

            generator._generate_prompt("test topic")

            # Check that system_prompt was provided
            call_kwargs = mock_router.generate.call_args[1]
            assert "system_prompt" in call_kwargs
            system_prompt = call_kwargs["system_prompt"]

            # Should mention DALL-E or image generation
            assert any(word in system_prompt.lower() for word in ["dalle", "image", "visual"])

    def test_call_gemini_api_success(self, mock_settings):
        """Test successful Gemini API call via OpenRouter.

        The API should:
        1. Send prompt to OpenRouter's chat completions endpoint
        2. Receive base64 image in response
        3. Return the data URL
        """
        generator = ImageGenerator()
        prompt = "A beautiful sunset over mountains"

        # Mock the HTTP request to OpenRouter
        with patch("src.images.generator.requests.post") as mock_post:
            # Setup mock response with Gemini format
            mock_response = Mock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "images": [
                                "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
                            ]
                        }
                    }
                ]
            }
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            # Call the method
            image_data = generator._call_gemini_api(prompt)

            # Verify the request
            mock_post.assert_called_once()
            call_args = mock_post.call_args

            # Should call OpenRouter API
            assert "openrouter.ai" in call_args[0][0]

            # Should send the prompt in messages format
            request_body = call_args[1]["json"]
            assert request_body["messages"][0]["content"] == prompt
            assert "modalities" in request_body
            assert "image" in request_body["modalities"]

            # Should include API key in headers
            headers = call_args[1]["headers"]
            assert "Authorization" in headers

            # Should return the base64 data URL
            assert image_data.startswith("data:image/png;base64,")

    def test_call_dalle_api_success(self, mock_settings):
        """Test successful DALL-E API call.

        The API should:
        1. Send prompt to OpenAI's DALL-E endpoint
        2. Receive image URL in response
        3. Return the URL
        """
        generator = ImageGenerator()
        prompt = "A beautiful sunset over mountains"

        # Mock the HTTP request
        with patch("src.images.generator.requests.post") as mock_post:
            # Setup mock response with DALL-E format
            mock_response = Mock()
            mock_response.json.return_value = {"data": [{"url": "https://example.com/image.png"}]}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            # Call the method
            image_url = generator._call_dalle_api(prompt)

            # Verify the request
            mock_post.assert_called_once()
            call_args = mock_post.call_args

            # Should call OpenAI API
            assert "api.openai.com" in call_args[0][0]

            # Should send the prompt in the body
            request_body = call_args[1]["json"]
            assert request_body["prompt"] == prompt

            # Should include API key in headers
            headers = call_args[1]["headers"]
            assert "Authorization" in headers

            # Should return the image URL
            assert image_url == "https://example.com/image.png"

    def test_call_dalle_api_uses_correct_parameters(self, mock_settings):
        """Test that DALL-E API call uses correct model parameters.

        Should use settings for:
        - Model (dall-e-3)
        - Size (1024x1024)
        - Quality (standard/hd)
        """
        generator = ImageGenerator()

        # Override settings to use DALL-E
        mock_settings.image_model = "dall-e-3"

        with patch("src.images.generator.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"data": [{"url": "https://example.com/img.png"}]}
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            # Call directly with model override
            generator._call_dalle_api("test prompt", model="dall-e-3")

            # Check request body parameters
            request_body = mock_post.call_args[1]["json"]
            assert request_body["model"] == "dall-e-3"
            assert request_body["size"] == "1024x1024"
            assert request_body.get("quality") == "standard"

    def test_call_dalle_api_handles_errors(self, mock_settings):
        """Test that API errors are handled gracefully.

        Should raise appropriate exceptions for:
        - Network errors
        - API errors
        - Invalid responses
        """
        generator = ImageGenerator()

        with patch("src.images.generator.requests.post") as mock_post:
            # Simulate API error
            mock_post.side_effect = requests.exceptions.RequestException("API Error")

            # Should raise an exception with specific message
            with pytest.raises(Exception, match="Failed to generate image"):
                generator._call_dalle_api("test prompt")

    def test_download_image_success(self, mock_settings, sample_image_bytes):
        """Test successful image download from URL.

        Should:
        1. Download image from URL
        2. Save to storage with post_id
        3. Return local file path
        """
        generator = ImageGenerator()
        image_url = "https://example.com/generated_image.png"
        post_id = 42

        # Mock the HTTP GET request
        with patch("src.images.generator.requests.get") as mock_get:
            # Setup mock response with image data
            mock_response = Mock()
            mock_response.content = sample_image_bytes
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # Call the method
            local_path = generator._download_image(image_url, post_id)

            # Verify the download
            mock_get.assert_called_once_with(image_url, timeout=30)

            # Verify file was saved
            assert Path(local_path).exists()
            assert f"post_{post_id}" in local_path

            # Verify it's a valid image
            img = Image.open(local_path)
            assert img.size == (10, 10)  # Our sample image size

    def test_download_image_handles_errors(self, mock_settings):
        """Test that download errors are handled gracefully."""
        generator = ImageGenerator()

        with patch("src.images.generator.requests.get") as mock_get:
            # Simulate network error
            mock_get.side_effect = requests.exceptions.RequestException("Download failed")

            # Should raise an exception with specific message
            with pytest.raises(Exception, match="Image download failed"):
                generator._download_image("https://example.com/image.png", 1)

    def test_generate_image_full_workflow(self, mock_settings, sample_image_bytes):
        """Test the full image generation workflow end-to-end.

        This is the orchestration method that:
        1. Generates optimized prompt from topic
        2. Calls Gemini API (since that's the default)
        3. Decodes base64 image
        4. Returns (image_path, prompt)

        This is what the agent nodes will call.
        """
        generator = ImageGenerator()
        topic = "Sustainable energy solutions"
        post_id = 100

        # Create base64 encoded test image
        base64_image = base64.b64encode(sample_image_bytes).decode("utf-8")
        data_url = f"data:image/png;base64,{base64_image}"

        # Mock all external calls
        with (
            patch("src.images.generator.LLMRouter") as mock_router_class,
            patch("src.images.generator.requests.post") as mock_post,
        ):

            # Mock LLM prompt generation
            mock_router = Mock()
            mock_router.generate.return_value = "Solar panels in a green field, photorealistic"
            mock_router_class.return_value = mock_router

            # Mock Gemini API call (default model is Gemini)
            mock_gemini_response = Mock()
            mock_gemini_response.json.return_value = {
                "choices": [{"message": {"images": [data_url]}}]
            }
            mock_gemini_response.raise_for_status = Mock()
            mock_post.return_value = mock_gemini_response

            # Call the main method
            image_path, prompt_used = generator.generate_image(topic, post_id)

            # Verify steps were called
            mock_router.generate.assert_called_once()
            mock_post.assert_called_once()

            # Verify results
            assert prompt_used == "Solar panels in a green field, photorealistic"
            assert Path(image_path).exists()
            assert f"post_{post_id}" in image_path

    def test_generate_image_with_custom_style(self, mock_settings, sample_image_bytes):
        """Test that the generate_image method works with custom parameters.

        The style parameter can be used for future enhancements.
        """
        generator = ImageGenerator()

        # Create base64 encoded test image
        base64_image = base64.b64encode(sample_image_bytes).decode("utf-8")
        data_url = f"data:image/png;base64,{base64_image}"

        with (
            patch("src.images.generator.LLMRouter") as mock_router_class,
            patch("src.images.generator.requests.post") as mock_post,
        ):

            # Setup mocks
            mock_router = Mock()
            mock_router.generate.return_value = "test prompt"
            mock_router_class.return_value = mock_router

            mock_gemini_response = Mock()
            mock_gemini_response.json.return_value = {
                "choices": [{"message": {"images": [data_url]}}]
            }
            mock_gemini_response.raise_for_status = Mock()
            mock_post.return_value = mock_gemini_response

            # Call with custom style (currently not used but parameter exists for future)
            image_path, prompt = generator.generate_image("test topic", 1, style="natural")

            # Verify it worked
            assert Path(image_path).exists()
            assert prompt == "test prompt"

    def test_get_image_path_finds_existing_image(self, mock_settings, sample_image_bytes):
        """Test that get_image_path can locate an existing image.

        This is useful for checking if a post already has an image
        before generating a new one.
        """
        generator = ImageGenerator()
        post_id = 77

        # Create a test image
        test_path = generator.storage_path / f"post_{post_id}.png"
        img = Image.new("RGB", (10, 10), color="green")
        img.save(test_path)

        # Should find it
        found_path = generator.get_image_path(post_id)
        assert found_path == str(test_path)

    def test_get_image_path_returns_none_if_not_found(self, mock_settings):
        """Test that get_image_path returns None for non-existent images."""
        generator = ImageGenerator()

        result = generator.get_image_path(999)
        assert result is None
