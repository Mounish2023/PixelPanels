"""API routes for comic generation."""
import asyncio
import json
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4
from click import style
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Request, Depends
from loguru import logger
import os
from datetime import datetime, timezone
from sqlalchemy.exc import NoResultFound
from sqlalchemy.sql.functions import now

from app.models.comic_models import (
    ComicProgress,
    StoryPrompt,
    ComicResponse,
    ComicStatus
)
from app.models.database import Comic, Panel, User, Like, View, Favorite, Trash
from app.database import get_db
from app.services.openai_service import OpenAIService
from app.services.media_service import MediaService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select



router = APIRouter()
jobs: Dict[str, ComicProgress] ={}

@router.post("/generate", response_model=ComicResponse)
async def start_comic_generation(
    story_prompt: StoryPrompt,
    user_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
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
            prompt_data_info={
                "style": story_prompt.style, 
                "num_panels": story_prompt.num_panels,
                "character_names":story_prompt.character_names},
            user_id=user_id,
            style=story_prompt.style
        )
        db.add(new_comic)
        await db.commit()
        await db.refresh(new_comic)

        jobs[job_id] = ComicProgress(
            id=job_id,
            status=ComicStatus.PENDING,
            current_step=0,
            total_steps=5,
            message="Starting comic generation...",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        # Start background task
        background_tasks.add_task(
            process_comic_generation,
            job_id=job_id,
            story_prompt=story_prompt
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

@router.get("/status/{job_id}", response_model=ComicProgress)
async def check_status(job_id: str, db: AsyncSession = Depends(get_db)) -> ComicProgress:
    """Check the status of a comic generation job."""

    if job_id not in jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # comic_result = await db.execute(select(Comic).filter(Comic.id == job_id))
    # comic = comic_result.scalars().first()
    # if not comic:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail=f"Job {job_id} not found"
    #     )
    
    # Retrieve the job status from the database
    return ComicProgress(
        id=job_id,
        status=jobs[job_id].status,
        current_step=jobs[job_id].current_step,
        total_steps=jobs[job_id].total_steps,
        message=jobs[job_id].message,
        created_at=jobs[job_id].created_at,
        updated_at=datetime.now(timezone.utc)
    )




async def process_comic_generation(job_id: str, story_prompt: StoryPrompt) -> None:
    """Process the comic generation in the background.
    
    Note: All generated files are preserved and never automatically deleted.
    """
    db: AsyncSession = Depends(get_db)
    try:
        if job_id not in jobs:
            raise NoResultFound
        jobs[job_id].status = ComicStatus.GENERATING_STORY
        jobs[job_id].updated_at = datetime.now(timezone.utc)
        jobs[job_id].current_step = 1
        jobs[job_id].message = "Generating story..."
        
        # Step 1: Generate story
        story = await OpenAIService.generate_story(
            prompt=story_prompt.prompt,
            style=story_prompt.style,
            character_names=story_prompt.character_names
        )
        
        # Update database with story
        try:
            comic_result = await db.execute(select(Comic).filter(Comic.id == job_id))
            comic = comic_result.scalars().first()
            if comic is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Comic with job ID {job_id} not found"
                )
                
            comic.story_text = story
            
            await db.commit()
            await db.refresh(comic)
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comic with job ID {job_id} not found"
            )


        try:
            if job_id not in jobs:
                raise NoResultFound
            jobs[job_id].status = ComicStatus.GENERATING_PANELS
            jobs[job_id].updated_at = datetime.now(timezone.utc)
            jobs[job_id].current_step = 2
            jobs[job_id].message = "Breaking story into panels..."
            # Step 2: Break story into panels
            panels_data = OpenAIService.break_story_into_panels(
                story=story,
                num_panels=story_prompt.num_panels
            )
            if comic.data_info is None:
                comic.data_info = {}

            # Update database with panel data
            comic.data_info['panels_data'] = panels_data
            await db.commit()
            await db.refresh(comic)
        except NoResultFound:            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comic with job ID {job_id} not found"
            )
        except Exception as e:
            jobs[job_id].status = ComicStatus.FAILED
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to break story into panels: {str(e)}"
            )
            
        

        try:
            if job_id not in jobs:
                raise NoResultFound
            jobs[job_id].status = ComicStatus.GENERATING_IMAGES
            jobs[job_id].updated_at = datetime.now(timezone.utc)
            jobs[job_id].current_step = 3
            jobs[job_id].message = "Generating panel images..."
            
            # Process all panels in parallel
            panel_tasks = [process_panel(job_id, panel_data, i) for i, panel_data in enumerate(panels_data)]
            panels = await asyncio.gather(*panel_tasks)

            comic.data_info.update({
                "panel_images": [panel.image_url for panel in panels]
            })
            # Bulk insert panels into database
            comic.thumbnail_url =panels[0].image_url
            db.add_all(panels)
            await db.commit()
            for panel in panels:
                await db.refresh(panel)
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comic with job ID {job_id} not found"
            )
        except Exception as e:
            jobs[job_id].status = ComicStatus.FAILED
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate panel images: {str(e)}"
            )
            
        try: 
            if job_id not in jobs:
                raise NoResultFound
                
            jobs[job_id].status = ComicStatus.GENERATING_AUDIO
            jobs[job_id].updated_at = datetime.now(timezone.utc)
            jobs[job_id].current_step = 4
            jobs[job_id].message = "Generating voiceover..."
                
            # Generate voiceover
            audio_data = await OpenAIService.generate_voiceover(story)
            
            # Save audio to Azure Blob Storage
            audio_path = f"comics/{job_id}/audio/voiceover.mp3"
            audio_blob_url = await MediaService.upload_audio(audio_data, audio_path)
            
            comic.audio_url = audio_blob_url
            comic.data_info.update({
                "audio_url": audio_blob_url,
                "completed_at": datetime.now(timezone.utc)
            })
            await db.commit()
            await db.refresh(comic)
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comic with job ID {job_id} not found"
            )
        except Exception as e:
            jobs[job_id].status = ComicStatus.FAILED
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate voiceover: {str(e)}"
            )
            
        jobs[job_id].status = ComicStatus.COMPLETED
        jobs[job_id].updated_at = datetime.now(timezone.utc)
        jobs[job_id].current_step = 5
        jobs[job_id].message = "Comic generation completed!"
        
    except Exception as e:
        logger.error(f"Error in comic generation: {str(e)}")
        raise

# Generate images for each panel in parallel
async def process_panel(job_id, panel_data, index):
    # Generate pixel art
    image_data = await OpenAIService.generate_pixel_art(
        description=panel_data["image_description"]
    )

    # Save to Azure Blob Storage
    image_path = f"comics/{job_id}/images/panel_{index+1}.png"
    blob_url = await MediaService.upload_image(image_data, image_path)

    return Panel(
        id = str(uuid4()),
        comic_id=job_id,
        sequence=index+1,
        text_content=panel_data["panel_text"],
        description=panel_data["image_description"],
        image_url=blob_url
    )

@router.get("/comics/{comic_id}/panels")
async def get_comic_panels(comic_id: int, db: AsyncSession = Depends(get_db)):
    """Get comic data with panels and metadata for display."""
    # Get comic with creator info in a single query
    query = (
        select(Comic, User.username.label("creator_name"))
        .join(User, Comic.user_id == User.id)
        .filter(Comic.id == comic_id)
    )
    result = await db.execute(query)
    comic_data = result.first()
    
    if not comic_data:
        raise HTTPException(status_code=404, detail="Comic not found")
        
    comic = comic_data.Comic
    creator_name = comic_data.creator_name
    
    # Get panels in sequence
    panels_query = select(Panel).filter(Panel.comic_id == comic_id).order_by(Panel.sequence)
    panels_result = await db.execute(panels_query)
    panels = panels_result.scalars().all()
    
    # Format response
    return {
        "comic_info": {
            "title": comic.title,
            "creator": creator_name,
            "like_count": comic.like_count,
            "view_count": comic.view_count,
            "audio_url": comic.audio_url,
        },
        "panels": [
            {
                "sequence": panel.sequence,
                "image_url": panel.image_url,
                "text_content": panel.text_content,
            }
            for panel in panels
        ],
        "total_panels": len(panels)
    }
