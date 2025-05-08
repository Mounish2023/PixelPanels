"""Image processing service for comic generation."""
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import base64
import textwrap

class ImageService:
    """Service for handling image processing operations."""
    
    @staticmethod
    async def upload_to_blob_storage(image_data: bytes, blob_name: str) -> str:
        """Upload image data to Object Storage and return the URL.
        
        Args:
            image_data: The image data in bytes
            blob_name: The name/path for the blob in storage
            
        Returns:
            The URL of the uploaded blob
        """
        try:
            from replit.object_storage import Client
            client = Client()
            
            # Upload the image data
            await asyncio.to_thread(
                client.upload_from_bytes,
                blob_name,
                image_data
            )
            
            # Get the public URL
            url = client.get_url(blob_name)
            return url
            
        except Exception as e:
            logger.error(f"Error uploading to storage: {str(e)}")
            raise
        
    
