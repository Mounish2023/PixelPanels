"""Pydantic models for the Comic Creator API."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ComicStatus(str, Enum):
    """Status of comic generation."""
    PENDING = "pending"
    GENERATING_STORY = "generating_story"
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

class Panel(BaseModel):
    """Represents a single panel in the comic."""
    panel_number: int
    image_description: str
    panel_text: str
    image_url: Optional[str] = None

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
