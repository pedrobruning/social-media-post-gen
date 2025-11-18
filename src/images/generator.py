"""Image generation supporting multiple models via OpenRouter and OpenAI.

This module handles generating images for social media posts. It supports:
- **Gemini 2.5 Flash Image** (Google) - FREE tier available
- **DALL-E 3** (OpenAI) - High quality, $0.04/image
- **DALL-E 2** (OpenAI) - Good quality, $0.02/image

The system automatically detects which API to use based on the IMAGE_MODEL
setting in your .env file. Just change the setting and it works!

Examples:
    # In .env:
    IMAGE_MODEL=google/gemini-2.5-flash-image-preview:free  # Use Gemini (FREE)
    IMAGE_MODEL=dall-e-3  # Use DALL-E 3
"""

import base64
import logging
import tempfile
from pathlib import Path

import requests

from src.config.settings import settings
from src.llm.router import LLMRouter

logger = logging.getLogger(__name__)


class ImageGenerator:
    """Multi-model image generator supporting Gemini and DALL-E.

    This class automatically routes to the appropriate image generation API
    based on your IMAGE_MODEL setting. It handles:
    - Generating image prompts from topics using LLM
    - Calling appropriate image API (Gemini or DALL-E)
    - Processing both base64 (Gemini) and HTTP URLs (DALL-E)
    - Storing images locally

    Supported Models:
    - google/gemini-2.5-flash-image (or -preview:free) → Gemini API
    - dall-e-3, dall-e-2 → DALL-E API

    Example:
        generator = ImageGenerator()
        image_path, prompt = generator.generate_image(
            topic="The future of AI",
            post_id=1
        )
        # Returns: ("storage/images/post_1.png", "A futuristic...")
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
        1. Uses LLM to generate optimized image prompt from topic
        2. Calls appropriate image generation API (auto-detected from model name)
        3. Saves the image locally
        4. Returns both the local path and the prompt used

        The system automatically detects whether to use DALL-E or Gemini based
        on the IMAGE_MODEL setting in .env.

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
            # Step 1: Generate optimized image prompt from topic using LLM
            prompt = self._generate_prompt(topic)
            logger.info(f"Generated prompt: {prompt}")

            # Step 2: Detect model type and call appropriate API
            model = settings.image_model

            if "gemini" in model.lower():
                # Gemini API: Returns base64 data URL
                logger.info(f"Using Gemini model: {model}")
                image_data = self._call_gemini_api(prompt)
                local_path = self._save_base64_image(image_data, post_id)

            elif "dall-e" in model.lower() or "dalle" in model.lower():
                # DALL-E API: Returns HTTP URL
                logger.info(f"Using DALL-E model: {model}")
                image_url = self._call_dalle_api(prompt)
                local_path = self._download_image(image_url, post_id)

            else:
                raise ValueError(
                    f"Unsupported image model: {model}. "
                    f"Supported models: DALL-E (dall-e-3, dall-e-2) or Gemini (google/gemini-*)"
                )

            logger.info(f"Image saved to: {local_path}")

            # Return both the local path and the prompt that was used
            # The prompt is stored in the database for reference
            return local_path, prompt

        except Exception as e:
            logger.error(f"Image generation failed for post {post_id}: {e}")
            raise Exception(f"Failed to generate image: {e}") from e

    def _generate_prompt(self, topic: str) -> str:
        """Generate an image prompt from a topic.

        This uses an LLM to convert a user topic into a detailed,
        visual prompt optimized for Gemini 2.5 Flash Image generation.

        Example:
            Input: "AI in healthcare"
            Output: "A futuristic medical facility with AI diagnostic systems,
                     holographic displays, warm lighting, professional photography"

        Args:
            topic: Post topic

        Returns:
            Optimized image generation prompt
        """
        # System prompt guides the LLM to create good image prompts
        system_prompt = """You are an expert at creating image generation prompts for AI models.

        Your task is to convert a topic into a detailed, visual prompt that will generate
        high-quality images suitable for social media posts (LinkedIn, Instagram, WordPress).

        Guidelines:
        - Be descriptive and visual (describe what you see, not concepts)
        - Include style guidance (e.g., "professional photography", "digital art", "photorealistic")
        - Include mood/atmosphere (e.g., "warm lighting", "vibrant colors", "minimalist")
        - Keep it concise but detailed (2-3 sentences max)
        - Focus on creating professional, eye-catching images
        - Avoid requesting text in the image
        - Think about composition, lighting, and visual appeal

        Return ONLY the prompt text, nothing else."""

        # User prompt provides the topic
        user_prompt = f"""Topic: {topic}

        Create a detailed image generation prompt for this topic:"""

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

    def _call_gemini_api(
        self,
        prompt: str,
        model: str | None = None,
        aspect_ratio: str | None = None,
    ) -> str:
        """Call Gemini image generation API via OpenRouter.

        Gemini uses OpenRouter's unified chat completions endpoint with
        special parameters for image generation. The response includes
        the generated image as a base64-encoded data URL.

        Args:
            prompt: Image generation prompt
            model: Model override (default from settings)
            aspect_ratio: Aspect ratio override (default from settings)
                         Options: 1:1, 3:4, 4:3, 9:16, 16:9

        Returns:
            Base64-encoded data URL of the generated image

        Raises:
            Exception: If API call fails
        """
        # Use provided values or fall back to settings
        model = model or settings.image_model
        aspect_ratio = aspect_ratio or settings.image_aspect_ratio

        # OpenRouter unified endpoint
        # Reference: https://openrouter.ai/docs/features/multimodal/image-generation
        url = "https://openrouter.ai/api/v1/chat/completions"

        # Prepare headers with API key
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/pedrobruning/social-media-post-gen",  # Optional but recommended
        }

        # Prepare request body for Gemini image generation
        # Gemini uses chat format with special modalities parameter
        body = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "modalities": ["image", "text"],  # Request both image and text output
            "image_config": {
                "aspect_ratio": aspect_ratio
            }
        }

        logger.info(f"Calling Gemini API with model={model}, aspect_ratio={aspect_ratio}")
        logger.debug(f"Prompt: {prompt}")

        try:
            # Make the API request
            response = requests.post(url, headers=headers, json=body, timeout=120)

            # Raise exception for HTTP errors
            response.raise_for_status()

            # Parse response
            data = response.json()

            # Extract image from response
            # Gemini returns images in the assistant message's 'images' field
            # as base64-encoded data URLs: "data:image/png;base64,..."
            assistant_message = data["choices"][0]["message"]

            if "images" not in assistant_message or len(assistant_message["images"]) == 0:
                raise Exception("No image returned in API response")

            # Get the first (and only) image
            image_data_url = assistant_message["images"][0]

            logger.info(f"Successfully generated image (base64 data URL)")
            return image_data_url

        except requests.exceptions.RequestException as e:
            logger.error(f"Gemini API call failed: {e}")
            raise Exception(f"Failed to generate image: {e}") from e
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse Gemini API response: {e}")
            logger.error(f"Response data: {data if 'data' in locals() else 'No response'}")
            raise Exception(f"Invalid API response: {e}") from e

    def _call_dalle_api(
        self,
        prompt: str,
        model: str | None = None,
        size: str | None = None,
        quality: str | None = None,
    ) -> str:
        """Call DALL-E API via OpenAI.

        DALL-E uses OpenAI's image generation endpoint. The response includes
        a temporary HTTP URL to download the generated image.

        Args:
            prompt: Image generation prompt
            model: Model override (default from settings)
            size: Size override (default from settings)
            quality: Quality override (default from settings)

        Returns:
            HTTP URL of the generated image

        Raises:
            Exception: If API call fails
        """
        # Use provided values or fall back to settings
        model = model or settings.image_model
        size = size or settings.image_size
        quality = quality or settings.image_quality

        # OpenAI DALL-E endpoint
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
        """Download image from HTTP URL and save locally.

        This method is used for DALL-E images which are served via HTTP URLs.

        Args:
            url: HTTP URL of the image
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

    def _save_base64_image(self, data_url: str, post_id: int) -> str:
        """Save a base64-encoded image to local storage.

        This method:
        1. Decodes the base64 data URL from Gemini
        2. Writes it to a temporary file
        3. Uses ImageStorage to copy it to the final location
        4. Returns the final local path

        Args:
            data_url: Base64-encoded data URL (format: "data:image/png;base64,...")
            post_id: Post ID for filename

        Returns:
            Local file path

        Raises:
            Exception: If decoding or save fails
        """
        logger.info(f"Processing base64 image data for post {post_id}")

        try:
            # Parse the data URL to extract the base64 content
            # Format: "data:image/png;base64,iVBORw0KGgoAAAANS..."
            if not data_url.startswith("data:"):
                raise ValueError("Invalid data URL format")

            # Split to get the base64 part
            # Example: "data:image/png;base64,..." -> ["data:image/png", "base64 content"]
            header, base64_data = data_url.split(",", 1)

            # Decode base64 to binary
            image_bytes = base64.b64decode(base64_data)

            # Create a temporary file to store the decoded image
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name

            logger.debug(f"Decoded image to temporary file: {temp_path}")

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

        except (ValueError, base64.binascii.Error) as e:
            logger.error(f"Failed to decode base64 image: {e}")
            raise Exception(f"Image decoding failed: {e}") from e
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
