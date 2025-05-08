"""API routes for comic generation."""
import asyncio
import json
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from loguru import logger
import os

from app.models.comic_models import (
    StoryPrompt,
    ComicProgress,
    ComicResponse,
    ComicStatus,
    Panel
)
from app.models.database import Comic
from app.database import get_db
from app.services.openai_service import OpenAIService
from app.services.image_service import ImageService
from app.utils.file_utils import create_project_dirs, cleanup_project
from app.config import settings
from fastapi.responses import FileResponse
import shutil
from sqlalchemy.orm import Session

router = APIRouter()

# In-memory storage for job progress (in production, use a database)
jobs: Dict[str, Dict[str, Any]] = {}

@router.post("/generate", response_model=ComicResponse)
async def start_comic_generation(
    story_prompt: StoryPrompt,
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> ComicResponse:
    """Start the comic generation process.
    
    This endpoint initiates the comic generation process in the background.
    """
    try:
        # Generate a unique ID for this job
        job_id = str(uuid4())
        
        # Create comic entry in database
        new_comic = Comic(
            id=job_id,
            title=story_prompt.prompt[:100],  # First 100 chars as title
            prompt=story_prompt.prompt,
            style=story_prompt.style,
            status=ComicStatus.PENDING,
            user_id=user_id,
            metadata={
                "character_names": story_prompt.character_names,
                "num_panels": story_prompt.num_panels
            }
        )
        db.add(new_comic)
        db.commit()
        
        # Initialize job progress
        jobs[job_id] = {
            "status": ComicStatus.PENDING,
            "progress": 0,
            "message": "Starting comic generation...",
            "story": None,
            "panels": [],
            "project_id": job_id
        }
        
        # Start background task
        background_tasks.add_task(
            process_comic_generation,
            job_id=job_id,
            story_prompt=story_prompt,
            db=db
        )
        
        return ComicResponse(
            success=True,
            message="Comic generation started",
            data={"job_id": job_id}
        )
    except Exception as e:
        logger.error(f"Error starting comic generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start comic generation: {str(e)}"
        )

@router.get("/status/{job_id}", response_model=ComicResponse)
async def check_status(job_id: str, db: Session = Depends(get_db)) -> ComicResponse:
    """Check the status of a comic generation job."""
    comic = db.query(Comic).filter(Comic.id == job_id).first()
    if not comic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Retrieve the job status from the database
    return ComicResponse(
        success=True,
        message="Job status retrieved",
        data={"status": comic.status}  # Now only getting status from the DB
    )

@router.get("/play/{job_id}", response_model=ComicResponse)
async def get_comic_data(job_id: str):
    """Get comic data for the frontend player."""
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = jobs[job_id]
    panels = job.get("panels", [])
    
    return {
        "success": True,
        "data": {
            "job_id": job_id,
            "panel_urls": [panel.get("image_url") for panel in panels if "image_url" in panel],
            "audio_url": job.get("audio_url", "")
        }
    }


@router.get(
    "/panel/{job_id}/{panel_index}",
    response_model=ComicResponse,
    summary="Fetch a single panel and its neighbors",
)
async def get_panel(job_id: str, panel_index: int):
    """
    Return the specified panel image URL plus the next/previous indices.
    """
    # 1) job exists?
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    panels = jobs[job_id].get("panels", [])
    total = len(panels)

    # 2) valid index?
    if panel_index < 1 or panel_index > total:
        raise HTTPException(
            status_code=400,
            detail=f"panel_index must be between 1 and {total}"
        )

    # 3) grab it
    panel = panels[panel_index - 1]
    panel_url = panel.get("image_url") or panel.get("image_path")
    if not panel_url:
        raise HTTPException(status_code=500, detail="Panel URL missing")

    # 4) compute prev / next
    prev_idx: Optional[int] = panel_index - 1 if panel_index > 1 else None
    next_idx: Optional[int] = panel_index + 1 if panel_index < total else None

    # 5) return via ComicResponse
    return ComicResponse(
        success=True,
        message="Panel fetched",
        data={
            "job_id": job_id,
            "panel_index": panel_index,
            "panel_url": panel_url,
            "prev_index": prev_idx,
            "next_index": next_idx,
            "total_panels": total,
        },
    )

@router.get("/share/{job_id}", response_model=ComicResponse)
async def get_share_data(job_id: str):
    """Get share data for the frontend."""
    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    job = jobs[job_id]
    
    # Check if video exists, if not create it
    video_path = Path(f"static/videos/{job_id}.mp4")
    if not video_path.exists():
        await create_video_from_panels(job_id, job)
    
    return {
        "success": True,
        "data": {
            "job_id": job_id,
            "video_url": f"/static/videos/{job_id}.mp4"
        }
    }

async def create_video_from_panels(job_id: str, job_data: dict):
    """Create a video from comic panels and audio."""
    try:
        import cv2
        import numpy as np
        from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips
        
        # Create output directory if it doesn't exist
        output_dir = Path("static/videos")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get panel images
        panels = job_data.get("panels", [])
        if not panels:
            raise ValueError("No panels available")
        
        # Create video clips for each panel
        clips = []
        for panel in panels:
            if "image_path" in panel:
                img = cv2.imread(panel["image_path"])
                if img is not None:
                    # Convert BGR to RGB
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    # Create a clip from the image (show each panel for 5 seconds)
                    clip = ImageSequenceClip([img], fps=1).set_duration(5)
                    clips.append(clip)
        
        if not clips:
            raise ValueError("No valid panel images found")
        
        # Concatenate all clips
        final_clip = concatenate_videoclips(clips, method="compose")
        
        # Add audio if available
        audio_path = job_data.get("audio_path")
        if audio_path and os.path.exists(audio_path):
            audio = AudioFileClip(audio_path)
            final_clip = final_clip.set_audio(audio)
        
        # Write the result to a file
        output_path = output_dir / f"{job_id}.mp4"
        final_clip.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True
        )
        
        # Clean up
        final_clip.close()
        
        # Update job with video URL
        job_data["video_url"] = f"/static/videos/{job_id}.mp4"
        
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise

async def process_comic_generation(job_id: str, story_prompt: StoryPrompt, db: Session) -> None:
    """Process the comic generation in the background.
    
    Note: All generated files are preserved and never automatically deleted.
    """
    try:
        # Create project directories
        base_dir, images_dir, audio_dir, output_dir = create_project_dirs(job_id)
        
        # Step 1: Generate story
        story = await OpenAIService.generate_story(
            prompt=story_prompt.prompt,
            style=story_prompt.style,
            character_names=story_prompt.character_names
        )
        
        # Update database with story
        comic = db.query(Comic).filter(Comic.id == job_id).first()
        comic.story_text = story
        comic.status = ComicStatus.GENERATING_IMAGES
        db.commit()
        
        # Step 2: Break story into panels
        panels_data = OpenAIService.break_story_into_panels(
            story=story,
            num_panels=story_prompt.num_panels
        )
        
        # Update database with panel data
        comic.data_info['panels_data'] = panels_data
        db.commit()
        
        # Generate images for each panel
        panels = []
        for i, panel_data in enumerate(panels_data):
            # Generate pixel art
            image_data = await OpenAIService.generate_pixel_art(
                description=panel_data["image_description"]
            )
            
            # Save to Azure Blob Storage
            image_path = f"comics/{job_id}/panel_{i+1}.png"
            blob_url = await ImageService.upload_to_blob_storage(image_data, image_path)
            
            # Save locally too
            local_path = images_dir / f"panel_{i+1}.png"
            with open(local_path, "wb") as f:
                f.write(image_data)
            
            # Create panel in database
            panel = Panel(
                comic_id=job_id,
                sequence=i+1,
                text_content=panel_data["panel_text"],
                description=panel_data["image_description"],
                image_url=blob_url
            )
            db.add(panel)
            panels.append(panel)
            db.commit()
            
        # Generate voiceover
        audio_data = await OpenAIService.generate_voiceover(story)
        
        # Save audio to Azure Blob Storage
        audio_path = f"comics/{job_id}/voiceover.mp3"
        audio_blob_url = await ImageService.upload_to_blob_storage(audio_data, audio_path)
        
        # Save locally too
        local_audio_path = audio_dir / "voiceover.mp3"
        with open(local_audio_path, "wb") as f:
            f.write(audio_data)
            
        # Update comic with final data
        comic.status = ComicStatus.COMPLETED
        comic.data_info.update({
            "audio_url": audio_blob_url,
            "completed_at": datetime.utcnow().isoformat()
        })
        db.commit()
        
        # Update job with story
        jobs[job_id].update({
            "story": story,
            "status": ComicStatus.GENERATING_IMAGES,
            "message": "Breaking story into panels...",
            "progress": 2
        })
        
        # Step 2: Break story into panels
        panels_data = OpenAIService.break_story_into_panels(
            story=story,
            num_panels=story_prompt.num_panels
        )
        
        # Save story data
        story_path = output_dir / "story.json"
        with open(story_path, 'w', encoding='utf-8') as f:
            json.dump({
                "prompt": story_prompt.dict(),
                "generated_story": story,
                "panels_data": panels_data
            }, f, indent=2, ensure_ascii=False)
        
        # Generate images for each panel
        panels = []
        for i, panel_data in enumerate(panels_data):
            jobs[job_id].update({
                "message": f"Generating image for panel {i+1}/{len(panels_data)}...",
                "progress": 3 + i
            })
            
            # Generate pixel art
            image_data = await OpenAIService.generate_pixel_art(
                description=panel_data["image_description"]
            )
            
            # Save the image
            image_path = images_dir / f"panel_{i+1}.png"
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            # Create panel object
            panel = Panel(
                panel_number=i+1,
                image_description=panel_data["image_description"],
                panel_text=panel_data["panel_text"],
                image_url=f"/api/v1/comics/files/{job_id}/images/panel_{i+1}.png"
            )
            panels.append(panel)
            
            # Save panel data
            panel_path = output_dir / f"panel_{i+1}.json"
            with open(panel_path, 'w', encoding='utf-8') as f:
                json.dump(panel.dict(), f, indent=2, ensure_ascii=False)
            
            # Update job with current panel
            jobs[job_id]["panels"] = [p.dict() for p in panels]
        
        # Step 3: Create comic page
        jobs[job_id].update({
            "message": "Creating comic page...",
            "progress": 4
        })
        
        comic_path = output_dir / "comic.png"
        ImageService.create_comic_page(
            images=[open(images_dir / f"panel_{i+1}.png", "rb").read() for i in range(len(panels))],
            panel_texts=[p.panel_text for p in panels],
            output_path=comic_path
        )
        
        # Step 4: Generate voiceover
        jobs[job_id].update({
            "message": "Generating voiceover...",
            "progress": 5
        })
        
        audio_path = output_dir / "voiceover.mp3"
        audio_data = await OpenAIService.generate_voiceover(story)
        with open(audio_path, "wb") as f:
            f.write(audio_data)
        
        # Update database and job progress
        comic = db.query(Comic).filter(Comic.id == job_id).first()
        comic.status = ComicStatus.COMPLETED
        comic.metadata.update({
            "story": story,
            "comic_url": f"/api/v1/comics/files/{job_id}/output/comic.png",
            "audio_url": f"/api/v1/comics/files/{job_id}/output/voiceover.mp3",
            "final_url": f"/comic/{job_id}"
        })
        db.commit()
        
        jobs[job_id].update({
            "status": ComicStatus.COMPLETED,
            "message": "Comic generation completed!",
            "comic_url": f"/api/v1/comics/files/{job_id}/output/comic.png",
            "audio_url": f"/api/v1/comics/files/{job_id}/output/voiceover.mp3",
            "final_url": f"/comic/{job_id}"
        })
        
    except Exception as e:
        logger.error(f"Error in comic generation: {str(e)}")
        if job_id in jobs:
            jobs[job_id].update({
                "status": ComicStatus.FAILED,
                "message": f"Failed to generate comic: {str(e)}"
            })
        # Never clean up project files - keep all outputs
        logger.info(f"Project files preserved at {base_dir}")
        raise

@router.get("/files/{project_id}/{file_type}/{filename}")
async def serve_file(project_id: str, file_type: str, filename: str):
    """Serve generated files."""
    try:
        file_path = settings.STORAGE_DIR / project_id / file_type / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(file_path)
    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to serve file")
