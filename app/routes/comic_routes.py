"""API routes for comic generation."""
import asyncio
import json
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from uuid import uuid4
from fastapi import APIRouter, HTTPException, BackgroundTasks, status, Request, Depends
from loguru import logger
import os
from datetime import datetime
from sqlalchemy.exc import NoResultFound

from app.models.comic_models import (
    StoryPrompt,
    ComicResponse,
    ComicStatus
)
from app.models.database import Comic, Panel
from app.database import get_db
from app.services.openai_service import OpenAIService
from app.services.image_service import ImageService
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter()

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
                "num_panels": story_prompt.num_panels},
            status=ComicStatus.PENDING,
            user_id=user_id,
            data_info={
                "character_names": story_prompt.character_names,
                "num_panels": story_prompt.num_panels
            }
        )
        db.add(new_comic)
        await db.commit()
        await db.refresh(new_comic)
        
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

@router.get("/status/{job_id}", response_model=ComicResponse)
async def check_status(job_id: str, db: AsyncSession = Depends(get_db)) -> ComicResponse:
    """Check the status of a comic generation job."""
    
    comic_result = await db.execute(select(Comic).filter(Comic.id == job_id))
    comic = comic_result.scalars().first()
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




async def process_comic_generation(job_id: str, story_prompt: StoryPrompt) -> None:
    """Process the comic generation in the background.
    
    Note: All generated files are preserved and never automatically deleted.
    """
    db: AsyncSession = Depends(get_db)
    try:
        
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
            comic.status = ComicStatus.GENERATING_STORY
            await db.commit()
            await db.refresh(comic)
        except NoResultFound:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Comic with job ID {job_id} not found"
            )

        try:
        
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
            
        
        # Generate images for each panel in parallel
        async def process_panel(panel_data, index):
            # Generate pixel art
            image_data = await OpenAIService.generate_pixel_art(
                description=panel_data["image_description"]
            )
            
            # Save to Azure Blob Storage
            image_path = f"comics/{job_id}/panel_{index+1}.png"
            blob_url = await ImageService.upload_to_blob_storage(image_data, image_path)
            
            return Panel(
                id = str(uuid4()),
                comic_id=job_id,
                sequence=index+1,
                text_content=panel_data["panel_text"],
                description=panel_data["image_description"],
                image_url=blob_url
            )

        # Process all panels in parallel
        panel_tasks = [process_panel(panel_data, i) for i, panel_data in enumerate(panels_data)]
        panels = await asyncio.gather(*panel_tasks)
        
        # Bulk insert panels into database
        db.add_all(panels)
        await db.commit()
        for panel in panels:
            await db.refresh(panel)
            
        # Generate voiceover
        audio_data = await OpenAIService.generate_voiceover(story)
        
        # Save audio to Azure Blob Storage
        audio_path = f"comics/{job_id}/voiceover.mp3"
        audio_blob_url = await ImageService.upload_to_blob_storage(audio_data, audio_path)
        
            
        # Update comic with final data
        comic.status = ComicStatus.COMPLETED
        comic.data_info.update({
            "audio_url": audio_blob_url,
            "completed_at": datetime.utcnow().isoformat()
        })
        await db.commit()
        
        # Update database and job progress
        # comic_result = await db.execute(select(Comic).filter(Comic.id == job_id))
        # comic = comic_result.scalars().first()
        comic.status = ComicStatus.COMPLETED
        comic.data_info.update({
            "story": story
        })
        await db.commit()
        
        
    except Exception as e:
        logger.error(f"Error in comic generation: {str(e)}")
        raise
@router.get("/comics/{comic_id}/panels")
async def get_comic_panels(comic_id: int, db: AsyncSession = Depends(get_db)):
    """Get all panels for a comic efficiently."""
    query = select(Panel).filter(Panel.comic_id == comic_id).order_by(Panel.sequence)
    result = await db.execute(query)
    panels = result.scalars().all()
    return panels
