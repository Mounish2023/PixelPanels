
"""Image processing service for comic generation."""
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple
from azure.storage.blob import BlobServiceClient
from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import base64
import textwrap
import asyncio
import os

class ImageService:
    """Service for handling image processing operations."""
    
    @staticmethod
    async def upload_to_blob_storage(image_data: bytes, blob_name: str) -> str:
        """Upload image data to Azure Blob Storage and return the URL.
        
        Args:
            image_data: The image data in bytes
            blob_name: The name/path for the blob in storage
            
        Returns:
            The URL of the uploaded blob
        """
        try:
            conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "comics")
            
            # Create the BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(conn_str)
            
            # Get container client
            container_client = blob_service_client.get_container_client(container_name)
            
            # Get blob client
            blob_client = container_client.get_blob_client(blob_name)
            
            # Upload the image data
            await asyncio.to_thread(
                blob_client.upload_blob,
                image_data,
                overwrite=True
            )
            
            # Get the blob URL
            url = blob_client.url
            return url
            
        except Exception as e:
            logger.error(f"Error uploading to Azure storage: {str(e)}")
            raise
