
"""Media processing service for comic generation."""
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple
from replit.object_storage import Client
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import base64
import textwrap
import asyncio
import os

class MediaService:
    """Service for handling media processing operations."""
    
    @staticmethod
    async def upload_to_storage(data: bytes, file_path: str) -> str:
        """Upload media data to Replit Object Storage and return the URL.
        
        Args:
            data: The media data in bytes (image or audio)
            file_path: The path/name for the file in storage
            
        Returns:
            The URL of the uploaded file
        """
        try:
            # Create Replit Object Storage client
            client = Client()
            
            # Upload the data
            await asyncio.to_thread(
                client.upload_bytes,
                file_path,
                data
            )
            
            # Get the file URL
            url = client.get_url(file_path)
            return url
            
        except Exception as e:
            logger.error(f"Error uploading to Replit storage: {str(e)}")
            raise

    @staticmethod
    async def upload_image(image_data: bytes, file_path: str) -> str:
        """Upload image data to storage."""
        return await MediaService.upload_to_storage(image_data, f"images/{file_path}")

    @staticmethod
    async def upload_audio(audio_data: bytes, file_path: str) -> str:
        """Upload audio data to storage."""
        return await MediaService.upload_to_storage(audio_data, f"audio/{file_path}")
