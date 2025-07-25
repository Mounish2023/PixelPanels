"""API routes for comic generation."""

import json
from typing import Any, Dict
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from loguru import logger
import os

from app.models.comic_models import (
    ComicProgress,
    StoryPrompt,
    ComicResponse,
    ComicStatus,
    Panel,
    StoryPrompt,
)
from app.models.database import Comic, Panel, User, Like, View, Favorite, Trash
from app.database import get_db
from app.services.openai_service import OpenAIService
from app.utils.file_utils import create_project_dirs
from app.database import BlobContainerClientSingleton

router = APIRouter()

# In-memory storage for job progress (in production, use a database)
jobs: Dict[str, Dict[str, Any]] = {}


@router.post("/generate", response_model=ComicResponse)
async def start_comic_generation(
    story_prompt: StoryPrompt, background_tasks: BackgroundTasks
) -> ComicResponse:
    """Start the comic generation process.

    This endpoint initiates the comic generation process in the background.
    """
    try:
        # Generate a unique ID for this job
        job_id = str(uuid4())

        # Initialize job progress
        jobs[job_id] = {
            "status": ComicStatus.PENDING,
            "progress": 0,
            "message": "Starting comic generation...",
            "story": None,
            "panels": [],
            "project_id": job_id,
        }

        # Start background task
        background_tasks.add_task(
            process_comic_generation, job_id=job_id, story_prompt=story_prompt
        )

        return ComicResponse(
            success=True, message="Comic generation started", data={"job_id": job_id}
        )
    except Exception as e:
        logger.error(f"Error starting comic generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start comic generation: {str(e)}",
        )


@router.get("/status/{job_id}", response_model=ComicResponse)
async def check_status(job_id: str) -> ComicResponse:
    """Check the status of a comic generation job."""

    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {job_id} not found"
        )

    job = jobs[job_id]

    # Create response model
    progress = ComicProgress(
        id=job_id,
        status=job["status"],
        current_step=job.get("progress", 0),
        total_steps=job.get("total_steps", 5),  # Adjust based on your steps
        message=job["message"],
        story=job.get("story"),
        panels=job.get("panels", []),
        comic_url=job.get("panel_image_urls"),
        final_output_url=job.get("final_output_url"),
        audio_url=job.get("audio_url"),
    )

    return ComicResponse(
        success=True, message="Job status retrieved", data=progress.model_dump()
    )


async def process_comic_generation(job_id: str, story_prompt: StoryPrompt) -> None:
    """Process the comic generation in the background.

    Note: All generated files are preserved and never automatically deleted.
    """
    try:
        # Create project directories
        base_dir, temp_dir, images_dir, audio_dir, output_dir = create_project_dirs(job_id)

        # Update job status
        jobs[job_id].update(
            {
                "status": ComicStatus.GENERATING_STORY,
                "message": "Generating story...",
                "progress": 1,
                "total_steps": 5,
            }
        )

        # Step 1: Generate story
        story = await OpenAIService.generate_story(
            prompt=story_prompt.prompt,
            style=story_prompt.style,
            character_names=story_prompt.character_names,
        )

        # Update job with story
        jobs[job_id].update(
            {
                "story": story,
                "status": ComicStatus.GENERATING_IMAGES,
                "message": "Breaking story into panels...",
                "progress": 2,
            }
        )

        # Step 2: Break story into panels
        panels_data = OpenAIService.break_story_into_panels(
            story=story, num_panels=story_prompt.num_panels
        )

        # Save story data
        # Upload story data to blob container
        blob_container = await BlobContainerClientSingleton.get_instance()
        await BlobContainerClientSingleton._upload_blob(
            blob_container,
            f"{temp_dir}/story.json",
            json.dumps(
                {
                    "prompt": story_prompt.model_dump(),
                    "generated_story": story,
                    "panels_data": panels_data,
                },
                indent=2,
                ensure_ascii=False,
            ),
        )

        # Generate images for each panel
        panels = []
        final_output = {}
        for i, panel_data in enumerate(panels_data):
            jobs[job_id].update(
                {
                    "message": f"Generating image for panel {i + 1}/{len(panels_data)}...",
                    "progress": 3,
                }
            )

            # Generate pixel art
            image_data = await OpenAIService.generate_pixel_art(
                description=panel_data["image_description"]
            )

            # Upload the image to blob container
            image_url = await BlobContainerClientSingleton._upload_blob(
                blob_container,
                f"{images_dir}/panel_{i + 1}.png",
                image_data,
            )

            # Create panel object
            panel = Panel(
                panel_number=i + 1,
                image_description=panel_data["image_description"],
                panel_text=panel_data["panel_text"],
                image_url=image_url,
            )
            panels.append(panel)

            final_output["panel_" + str(i + 1)] = panel.image_url

            # Update job with current panel
            jobs[job_id]["panels"] = [p.model_dump() for p in panels]

        # Step 4: Generate voiceover
        jobs[job_id].update({"message": "Generating voiceover...", "progress": 4})

        audio_data = await OpenAIService.generate_voiceover(story)
        
        # Upload audio to blob container
        audio_url = await BlobContainerClientSingleton._upload_blob(
            blob_container,
            f"{audio_dir}/voiceover.mp3",
            audio_data,
        )

        final_output["audio_url"] = audio_url

        # Upload final output to blob container
        final_output_url = await BlobContainerClientSingleton._upload_blob(
            blob_container,
            f"{output_dir}/final_output.json",
            json.dumps(final_output, indent=2, ensure_ascii=False),
        )

        # Update job with final URLs
        jobs[job_id].update(
            {
                "status": ComicStatus.COMPLETED,
                "message": "Comic generation completed!",
                "panel_image_urls": [panel.image_url for panel in panels],
                "audio_url": audio_url,
                "final_output_url": final_output_url,
            }
        )

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
