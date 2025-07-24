"""File handling utilities."""

import shutil

from pathlib import Path
from typing import Tuple
from loguru import logger

from app.config import settings

def sanitize_filename(filename: str) -> str:
    """Convert string to a valid filename."""
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_')).rstrip()

def create_project_dirs(project_id: str) -> Tuple[Path, Path, Path, Path]:
    """Create project directories.
    
    Args:
        project_id: Unique identifier for the project
        
    Returns:
        Tuple of (base_dir, images_dir, audio_dir, output_dir)
    """
    base_dir = Path(project_id)
    temp_dir = base_dir / "temp"
    images_dir = base_dir / "images"
    audio_dir = base_dir / "audio"
    output_dir = base_dir / "output"
    
    for dir_path in [base_dir, temp_dir, images_dir, audio_dir, output_dir]:
        dir_path.mkdir(exist_ok=True, parents=True)
    
    return base_dir, temp_dir, images_dir, audio_dir, output_dir

def cleanup_project(project_id: str) -> bool:
    """Remove all files and directories for a project."""
    try:
        project_dir = settings.STORAGE_DIR / project_id
        if project_dir.exists() and project_dir.is_dir():
            shutil.rmtree(project_dir)
            return True
        return False
    except Exception as e:
        logger.error(f"Error cleaning up project {project_id}: {str(e)}")
        return False

def get_file_extension(content_type: str) -> str:
    """Get file extension from content type."""
    content_type_map = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "audio/mpeg": ".mp3",
        "audio/wav": ".wav",
    }
    return content_type_map.get(content_type.lower(), ".bin")
