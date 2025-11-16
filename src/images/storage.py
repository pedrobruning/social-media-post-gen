"""Image storage utilities for managing generated images.

This module provides utilities for storing, retrieving, and managing
generated social media post images.
"""

import shutil
from pathlib import Path
from typing import Optional

from src.config.settings import settings


class ImageStorage:
    """Utility class for managing image storage.
    
    Handles storing, retrieving, and deleting images from local filesystem.
    Can be extended to support cloud storage (S3, etc.) in the future.
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        """Initialize image storage.
        
        Args:
            storage_path: Path to storage directory (default from settings)
        """
        self.storage_path = Path(storage_path or settings.image_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_image(self, source_path: str, post_id: int, format: str = "png") -> str:
        """Save an image to storage.
        
        Args:
            source_path: Path to source image file
            post_id: Post database ID
            format: Image format (png, jpg, webp)
            
        Returns:
            Path to saved image
        """
        # TODO: Implement image saving
        pass
    
    def get_image(self, post_id: int) -> Optional[str]:
        """Get image path for a post.
        
        Args:
            post_id: Post database ID
            
        Returns:
            Image path if exists, None otherwise
        """
        # Check for different formats
        for ext in ['png', 'jpg', 'jpeg', 'webp']:
            path = self.storage_path / f"post_{post_id}.{ext}"
            if path.exists():
                return str(path)
        return None
    
    def delete_image(self, post_id: int) -> bool:
        """Delete an image from storage.
        
        Args:
            post_id: Post database ID
            
        Returns:
            True if deleted, False if not found
        """
        image_path = self.get_image(post_id)
        if image_path:
            Path(image_path).unlink()
            return True
        return False
    
    def get_image_url(self, post_id: int, base_url: str = "") -> Optional[str]:
        """Get the public URL for an image.
        
        Args:
            post_id: Post database ID
            base_url: Base URL for the API
            
        Returns:
            Public URL for the image
        """
        if self.get_image(post_id):
            return f"{base_url}/api/posts/{post_id}/image"
        return None

