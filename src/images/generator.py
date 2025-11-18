"""Image generation using DALL-E 3 via OpenRouter.

This module handles generating images for social media posts using DALL-E 3.
Images are generated based on the post topic and stored locally.
"""

import logging
import tempfile
from pathlib import Path

import requests

from src.config.settings import settings
from src.llm.router import LLMRouter

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generator for creating images using DALL-E 3 via OpenRouter.

    This class handles:
    - Generating image prompts from topics
    - Calling DALL-E 3 API via OpenRouter
    - Downloading and storing images locally

    Example:
        generator = ImageGenerator()
        image_path, prompt = generator.generate_image(
            topic="The future of AI",
            post_id=1
        )
    """

    def __init__(self):
        """Initialize the image generator."""
        self.storage_path = Path(settings.image_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def generate_image(
        self,
        topic: str,
        post_id: int,
        style: str | None = None,
    ) -> tuple[str, str]:
        """Generate an image for a post topic.

        This is the main orchestration method that:
        1. Uses LLM to generate optimized DALL-E prompt from topic
        2. Calls DALL-E 3 API to generate the image
        3. Downloads and saves the image locally
        4. Returns both the local path and the prompt used

        The agent nodes will call this method during workflow execution.

        Args:
            topic: The post topic to generate an image for
            post_id: Database ID of the post (for filename)
            style: Image style override (default from settings)

        Returns:
            Tuple of (image_path, prompt_used)

        Raises:
            Exception: If any step in the generation process fails
        """
        logger.info(f"Starting image generation for topic: {topic}")

        try:
            # Step 1: Generate optimized DALL-E prompt from topic
            prompt = self._generate_prompt(topic)
            logger.info(f"Generated prompt: {prompt}")

            # Step 2: Call DALL-E API to generate the image
            # Note: style parameter could be used here if we want to override
            # For now, we use settings defaults
            image_url = self._call_dalle_api(prompt)
            logger.info(f"Received image URL: {image_url}")

            # Step 3: Download and save the image
            local_path = self._download_image(image_url, post_id)
            logger.info(f"Image saved to: {local_path}")

            # Return both the local path and the prompt that was used
            # The prompt is stored in the database for reference
            return local_path, prompt

        except Exception as e:
            logger.error(f"Image generation failed for post {post_id}: {e}")
            raise Exception(f"Failed to generate image: {e}") from e

    def _generate_prompt(self, topic: str) -> str:
        """Generate a DALL-E prompt from a topic.

        This uses an LLM to convert a user topic into a detailed,
        visual prompt optimized for DALL-E image generation.

        Example:
            Input: "AI in healthcare"
            Output: "A futuristic medical facility with AI diagnostic systems,
                     holographic displays, warm lighting, professional photography"

        Args:
            topic: Post topic

        Returns:
            Optimized DALL-E prompt
        """
        # System prompt guides the LLM to create good DALL-E prompts
        system_prompt = """You are an expert at creating image generation prompts for DALL-E 3.

        Your task is to convert a topic into a detailed, visual prompt that will generate
        high-quality images suitable for social media posts (LinkedIn, Instagram, WordPress).

        Guidelines:
        - Be descriptive and visual (describe what you see, not concepts)
        - Include style guidance (e.g., "professional photography", "digital art", "photorealistic")
        - Include mood/atmosphere (e.g., "warm lighting", "vibrant colors", "minimalist")
        - Keep it under 400 characters (DALL-E's limit)
        - Focus on creating professional, eye-catching images
        - Avoid text in the image (DALL-E struggles with text)

        Return ONLY the prompt text, nothing else."""

        # User prompt provides the topic
        user_prompt = f"""Topic: {topic}

        Create a detailed DALL-E prompt for this topic:"""

        # Use LLM router to generate the prompt
        router = LLMRouter(
            temperature=0.7  # Some creativity, but not too wild
        )

        optimized_prompt = router.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=150  # Prompts should be concise
        )

        logger.info(f"Generated DALL-E prompt: {optimized_prompt}")
        return optimized_prompt.strip()

    def _call_dalle_api(
        self,
        prompt: str,
        model: str | None = None,
        size: str | None = None,
        quality: str | None = None,
    ) -> str:
        """Call DALL-E API via OpenRouter.

        OpenRouter provides access to DALL-E using OpenAI's format.
        We send a POST request with the prompt and receive back an image URL.

        Args:
            prompt: Image generation prompt
            model: Model override (default from settings)
            size: Size override (default from settings)
            quality: Quality override (default from settings)

        Returns:
            URL of the generated image

        Raises:
            Exception: If API call fails
        """
        # Use provided values or fall back to settings
        model = model or settings.image_model
        size = size or settings.image_size
        quality = quality or settings.image_quality

        # OpenRouter uses OpenAI-compatible endpoint for DALL-E
        # Reference: https://openrouter.ai/docs#dall-e
        url = "https://api.openai.com/v1/images/generations"

        # Prepare headers with API key
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json"
        }

        # Prepare request body
        body = {
            "model": model,
            "prompt": prompt,
            "n": 1,  # Generate 1 image
            "size": size,
            "quality": quality,
        }

        logger.info(f"Calling DALL-E API with model={model}, size={size}, quality={quality}")

        try:
            # Make the API request
            response = requests.post(url, headers=headers, json=body, timeout=60)

            # Raise exception for HTTP errors
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract image URL from response
            # Response format: {"data": [{"url": "https://..."}]}
            image_url = data["data"][0]["url"]

            logger.info(f"Successfully generated image: {image_url}")
            return image_url

        except requests.exceptions.RequestException as e:
            logger.error(f"DALL-E API call failed: {e}")
            raise Exception(f"Failed to generate image: {e}") from e
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse DALL-E API response: {e}")
            raise Exception(f"Invalid API response: {e}") from e

    def _download_image(self, url: str, post_id: int) -> str:
        """Download image from URL and save locally.

        This method:
        1. Downloads the image from the DALL-E URL
        2. Saves it to a temporary file
        3. Uses ImageStorage to copy it to the final location
        4. Returns the final local path

        Args:
            url: Image URL from DALL-E
            post_id: Post ID for filename

        Returns:
            Local file path

        Raises:
            Exception: If download or save fails
        """
        logger.info(f"Downloading image from {url}")

        try:
            # Download the image
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # Create a temporary file to store the downloaded image
            # DALL-E returns PNG images
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name

            # Use ImageStorage to save to final location
            from src.images.storage import ImageStorage
            storage = ImageStorage()
            final_path = storage.save_image(
                source_path=temp_path,
                post_id=post_id,
                format=settings.image_format
            )

            # Clean up temporary file
            Path(temp_path).unlink()

            logger.info(f"Image saved to {final_path}")
            return final_path

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download image: {e}")
            raise Exception(f"Image download failed: {e}") from e
        except Exception as e:
            logger.error(f"Failed to save image: {e}")
            raise Exception(f"Image save failed: {e}") from e

    def get_image_path(self, post_id: int) -> str | None:
        """Get the local path for a post's image.

        Args:
            post_id: Post database ID

        Returns:
            Image path if exists, None otherwise
        """
        # Check for different formats
        for ext in ["png", "jpg", "jpeg", "webp"]:
            path = self.storage_path / f"post_{post_id}.{ext}"
            if path.exists():
                return str(path)
        return None
