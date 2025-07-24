"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings."""
    
    # Application settings
    APP_NAME: str 
    DEBUG: bool 
    
    # API settings
    API_V1_STR: str 
    SECRET_KEY: str 
    
    # OpenAI settings
    OPENAI_API_KEY: str 

    # Storage settings
    # STORAGE_DIR: Path = Path("./storage")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Azure Storage settings
    AZURE_STORAGE_CONNECTION_STRING: str 
    AZURE_STORAGE_CONTAINER_NAME: str 
    STORAGE_ACCOUNT_NAME: str 
    STORAGE_ACCOUNT_KEY: str 
    
    model_config = SettingsConfigDict(
        case_sensitive = True,
        extra = "ignore",
        env_file=".env"
    )

# Initialize settings
settings = Settings()

# Create storage directory if it doesn't exist
# settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
