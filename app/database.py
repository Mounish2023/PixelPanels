import asyncio
from azure.storage.blob.aio import BlobServiceClient
from app.config import settings


class BlobContainerClientSingleton:
    _instance = None

    @classmethod
    async def get_instance(cls):
        if cls._instance is None:
            cls._instance = await cls._create_instance()
            print("BlobContainerClientSingleton instance created")
        return cls._instance

    @classmethod
    async def _create_instance(cls):
        blob_service_client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )
        container_client = blob_service_client.get_container_client(
            settings.AZURE_STORAGE_CONTAINER_NAME
        )
        return container_client

    @classmethod
    async def _upload_blob(cls, blob_container_client, blob_name, data):
        blob_client = blob_container_client.get_blob_client(blob_name)
        await blob_client.upload_blob(data, overwrite=True)
        return blob_client.url

    @classmethod
    async def close_instance(cls):
        if cls._instance is not None:
            await cls._instance.close()
            print("BlobContainerClientSingleton instance closed")
            cls._instance = None

async def test_upload_blob():
    blob_container_client = await BlobContainerClientSingleton.get_instance()
    blob_name = "test.txt"
    data = b"Hello, world!"
    url = await BlobContainerClientSingleton._upload_blob(
        blob_container_client, blob_name, data
    )
    assert url is not None

if __name__ == "__main__":
    asyncio.run(test_upload_blob())
