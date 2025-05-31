"""Application configuration settings."""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    APP_NAME: str = "PixelPanels"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/pixelpanels")
    STORAGE_ACCOUNT_URL: str = os.getenv("STORAGE_ACCOUNT_URL", "")
    STORAGE_ACCOUNT_KEY: str = os.getenv("STORAGE_ACCOUNT_KEY", "")
    STORAGE_ACCOUNT_NAME: str = os.getenv("STORAGE_ACCOUNT_NAME", "")
    CONTAINER_NAME: str = os.getenv("CONTAINER_NAME", "comics")
    
    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # OpenAI settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Storage settings
    STORAGE_DIR: Path = Path("./storage")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        case_sensitive = True

# Initialize settings
settings = Settings()

# Create storage directory if it doesn't exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
