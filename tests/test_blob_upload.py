import asyncio
from azure.storage.blob.aio import BlobServiceClient
from app.config import settings

async def test_upload_blob():
    job_id = "test-job"
    blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container="comics", blob=f"{job_id}/test.txt")
    data = b"Hello, world!"
    await blob_client.upload_blob(data, overwrite=True)
    assert await blob_client.exists()
    print("Blob uploaded successfully")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_upload_blob())
