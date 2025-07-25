"""Pydantic models for the Comic Creator API."""
from google.cloud.storage import bucket
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas
from config import settings

class ComicStatus(str, Enum):
    """Status of comic generation."""
    PENDING = "pending"
    GENERATING_STORY = "generating_story"
    GENERATING_PANELS ="generating_panels"
    GENERATING_IMAGES = "generating_images"
    GENERATING_AUDIO = "generating_audio"
    COMPLETED = "completed"
    FAILED = "failed"

class StoryPrompt(BaseModel):
    """Request model for generating a comic story."""
    prompt: str = Field(..., description="The main prompt for the story")
    style: str = Field("child-friendly fantasy", description="Style of the story")
    character_names: Optional[List[str]] = Field(None, description="List of character names to include")
    num_panels: int = Field(10, description="Number of panels in the comic", ge=1, le=20)

class ComicProgress(BaseModel):
    """Response model for comic generation progress."""
    id: str
    status: ComicStatus
    current_step: int
    total_steps: int
    message: str
    story: Optional[str] = None
    panels: Optional[List[Panel]] = None
    panel_image_urls: Optional[List[str]] = None
    audio_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        use_enum_values = True

class ComicResponse(BaseModel):
    """Response model for comic generation result."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class searchComicResponse(BaseModel):
    """Response model for comic search result."""
    id: int
    title: str
    thumbnail_url: str
    view_count: int
    created_at: datetime
    creator: str

    @model_validator(mode='before')
    def build_thumbnail_url(cls, values):
        if values.get("thumbnail_url"):
            values["thumbnail_url"] = make_thumbnail_url(values["thumbnail_url"])
        return values

def make_thumbnail_url(thumbnail_url: str) -> str:
    sas_token = generate_blob_sas(
        account_name=settings.STORAGE_ACCOUNT_NAME,
        container_name=settings.CONTAINER_NAME,
        account_key=settings.STORAGE_ACCOUNT_KEY,
        blob_name=thumbnail_url,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.now(timezone.utc) + timedelta(hours=1)  # Token valid for 1 hour
    )
    container_name = settings.CONTAINER_NAME

    return f"https://{settings.STORAGE_ACCOUNT_NAME}.blob.core.windows.net/{container_name}/{thumbnail_url}?{sas_token}"

