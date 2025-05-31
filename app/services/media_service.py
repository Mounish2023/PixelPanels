
"""Media processing service for comic generation."""

from azure.storage.blob.aio import BlobServiceClient, ContentSettings
from loguru import logger
import asyncio


class MediaService:
    """Service for handling media processing operations using Azure Blob Storage."""
    
    @staticmethod
    async def upload_to_storage(data: bytes, container_name: str, blob_name: str, connection_string: str) -> str:
        """Upload media data to Azure Blob Storage and return the URL.
        
        Args:
            data: The media data in bytes (image or audio)
            container_name: The name of the Azure Blob Storage container
            blob_name: The name of the blob
            connection_string: The connection string for Azure Blob Storage
            
        Returns:
            The URL of the uploaded blob
        """
        try:
            # Create BlobServiceClient using the connection string
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            
            # Get the container client
            container_client = blob_service_client.get_container_client(container_name)
            
            # Upload the data
            await asyncio.to_thread(
                container_client.upload_blob,
                name=blob_name,
                data=data,
                overwrite=True,
                content_settings=ContentSettings(content_type='application/octet-stream')
            )
            
            # Get the blob URL
            blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
            return blob_url
            
        except Exception as e:
            logger.error(f"Error uploading to Azure Blob Storage: {str(e)}")
            raise

    @staticmethod
    async def upload_image(image_data: bytes, container_name: str, blob_name: str, connection_string: str) -> str:
        """Upload image data to storage using Azure Blob Storage."""
        return await MediaService.upload_to_storage(image_data, container_name, blob_name, connection_string)

    @staticmethod
    async def upload_audio(audio_data: bytes, container_name: str, blob_name: str, connection_string: str) -> str:
        """Upload audio data to storage using Azure Blob Storage."""
        return await MediaService.upload_to_storage(audio_data, container_name, blob_name, connection_string)
