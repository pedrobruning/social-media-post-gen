"""Tests for image storage functionality.

This module tests the ImageStorage class for saving, retrieving, and
deleting images from local filesystem storage.
"""

import shutil
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from src.images.storage import ImageStorage


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing.

    This fixture:
    1. Creates a temporary directory
    2. Provides it to the test
    3. Cleans it up after the test finishes

    Yields:
        Path: Temporary storage directory path
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_image(temp_storage):
    """Create a sample test image.

    This creates a simple 100x100 red image for testing purposes.

    Args:
        temp_storage: Temporary storage directory from fixture

    Returns:
        str: Path to the created test image
    """
    # Create a simple 100x100 red image
    img = Image.new("RGB", (100, 100), color="red")
    image_path = Path(temp_storage) / "test_image.png"
    img.save(image_path)
    return str(image_path)


class TestImageStorage:
    """Test suite for ImageStorage class."""

    def test_init_creates_directory(self, temp_storage):
        """Test that initializing storage creates the directory if it doesn't exist.

        Why this matters: We need to ensure the storage directory exists
        before trying to save images to it.
        """
        storage_path = Path(temp_storage) / "new_storage"
        assert not storage_path.exists()

        _ = ImageStorage(str(storage_path))

        assert storage_path.exists()
        assert storage_path.is_dir()

    def test_save_image_creates_file(self, temp_storage, sample_image):
        """Test that save_image successfully copies an image to storage.

        This is the core functionality - taking a temporary image and
        saving it with a standardized name (post_<id>.png).
        """
        storage = ImageStorage(temp_storage)
        post_id = 42

        # Save the image
        saved_path = storage.save_image(sample_image, post_id, format="png")

        # Verify it was saved
        assert Path(saved_path).exists()
        assert saved_path == str(Path(temp_storage) / "post_42.png")

    def test_save_image_overwrites_existing(self, temp_storage, sample_image):
        """Test that saving an image overwrites an existing image for the same post.

        Why this matters: If we regenerate a post's image, we want to
        replace the old one, not create duplicates.
        """
        storage = ImageStorage(temp_storage)
        post_id = 1

        # Save image first time
        first_save = storage.save_image(sample_image, post_id)

        # Create a different image (blue instead of red)
        img = Image.new("RGB", (100, 100), color="blue")
        new_image_path = Path(temp_storage) / "new_test_image.png"
        img.save(new_image_path)

        # Save again with same post_id
        second_save = storage.save_image(str(new_image_path), post_id)

        # Should be same path
        assert first_save == second_save

        # Should only have one file
        png_files = list(Path(temp_storage).glob("post_1.*"))
        assert len(png_files) == 1

    def test_save_image_different_formats(self, temp_storage, sample_image):
        """Test saving images in different formats (png, jpg, webp).

        Different platforms may prefer different formats:
        - PNG: Best quality, transparency support
        - JPEG: Smaller file size
        - WebP: Modern format, good compression
        """
        storage = ImageStorage(temp_storage)

        # Test PNG
        png_path = storage.save_image(sample_image, post_id=1, format="png")
        assert png_path.endswith(".png")
        assert Path(png_path).exists()

        # Test JPEG
        jpg_path = storage.save_image(sample_image, post_id=2, format="jpg")
        assert jpg_path.endswith(".jpg")
        assert Path(jpg_path).exists()

    def test_get_image_existing(self, temp_storage, sample_image):
        """Test retrieving an existing image path.

        This method is used to check if a post already has an image
        and get its path for serving via API.
        """
        storage = ImageStorage(temp_storage)
        post_id = 5

        # Save an image
        storage.save_image(sample_image, post_id)

        # Retrieve it
        retrieved_path = storage.get_image(post_id)

        assert retrieved_path is not None
        assert Path(retrieved_path).exists()
        assert "post_5" in retrieved_path

    def test_get_image_not_found(self, temp_storage):
        """Test that get_image returns None for non-existent images.

        This is important for error handling - we need to know when
        an image doesn't exist without raising an exception.
        """
        storage = ImageStorage(temp_storage)

        result = storage.get_image(post_id=999)

        assert result is None

    def test_get_image_finds_different_formats(self, temp_storage, sample_image):
        """Test that get_image can find images regardless of format.

        We might not know what format the image was saved in,
        so get_image should check all common formats.
        """
        storage = ImageStorage(temp_storage)

        # Save as JPEG
        storage.save_image(sample_image, post_id=10, format="jpg")

        # Should still find it
        found_path = storage.get_image(10)
        assert found_path is not None
        assert found_path.endswith(".jpg")

    def test_delete_image_existing(self, temp_storage, sample_image):
        """Test deleting an existing image.

        Used for cleanup when a post is deleted or regenerated.
        """
        storage = ImageStorage(temp_storage)
        post_id = 7

        # Save an image
        saved_path = storage.save_image(sample_image, post_id)
        assert Path(saved_path).exists()

        # Delete it
        result = storage.delete_image(post_id)

        assert result is True
        assert not Path(saved_path).exists()

    def test_delete_image_not_found(self, temp_storage):
        """Test deleting a non-existent image returns False.

        Should gracefully handle deletion of images that don't exist.
        """
        storage = ImageStorage(temp_storage)

        result = storage.delete_image(post_id=999)

        assert result is False

    def test_get_image_url(self, temp_storage, sample_image):
        """Test generating public URLs for images.

        This creates API URLs like: http://api.com/api/posts/5/image
        Used by the frontend to display images.
        """
        storage = ImageStorage(temp_storage)
        post_id = 8
        base_url = "http://localhost:8000"

        # Save an image
        storage.save_image(sample_image, post_id)

        # Get URL
        url = storage.get_image_url(post_id, base_url)

        assert url == f"{base_url}/api/posts/{post_id}/image"

    def test_get_image_url_no_image(self, temp_storage):
        """Test that get_image_url returns None if image doesn't exist.

        Prevents broken image links in API responses.
        """
        storage = ImageStorage(temp_storage)

        url = storage.get_image_url(post_id=999, base_url="http://test.com")

        assert url is None
