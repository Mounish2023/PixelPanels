"""
Comic Creator App - Backend
Uses FastAPI and OpenAI to generate stories, pixel art, and voice overs for children's comics
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import os
import openai
import uuid
import json
import asyncio
from pathlib import Path
from typing import List, Optional
import base64
import shutil
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io
import tempfile
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Comic Creator")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class StoryPrompt(BaseModel):
    prompt: str
    style: Optional[str] = "child-friendly fantasy"
    character_names: Optional[List[str]] = None
    num_panels: Optional[int] = 10

class ComicProgress(BaseModel):
    id: str
    status: str
    current_step: int
    total_steps: int
    message: str
    story: Optional[str] = None
    panels: Optional[List[dict]] = None
    comic_url: Optional[str] = None
    audio_url: Optional[str] = None
    final_url: Optional[str] = None

# In-memory storage for job progress
# In production, use a proper database
job_progress = {}

# Initialize OpenAI client
# Replace with your API key or use environment variable
openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-api-key"))

# Configure storage paths
STORAGE_DIR = Path("./storage")
STORAGE_DIR.mkdir(exist_ok=True)

# Helper functions
def sanitize_filename(name):
    """Convert string to valid filename"""
    return "".join(c for c in name if c.isalnum() or c in (' ', '.', '_')).rstrip()

def create_project_dirs(project_id):
    """Create project directories"""
    base_dir = STORAGE_DIR / project_id
    images_dir = base_dir / "images"
    audio_dir = base_dir / "audio"
    output_dir = base_dir / "output"
    
    for dir_path in [base_dir, images_dir, audio_dir, output_dir]:
        dir_path.mkdir(exist_ok=True, parents=True)
    
    return base_dir, images_dir, audio_dir, output_dir

def update_progress(project_id, status, step, total, message, **kwargs):
    """Update job progress"""
    job_progress[project_id] = {
        "id": project_id,
        "status": status,
        "current_step": step,
        "total_steps": total,
        "message": message,
        **kwargs
    }
    logger.info(f"Project {project_id}: {status} - {message}")

async def generate_story(prompt, style, character_names=None):
    """Generate a short story using OpenAI"""
    character_prompt = ""
    if character_names:
        character_prompt = f"Include these characters: {', '.join(character_names)}. "
    
    system_prompt = f"""Create a short, engaging children's story in the style of {style}. 
    The story should be appropriate for children, with a clear beginning, middle, and end.
    {character_prompt}
    Keep it concise yet engaging, suitable for a 10-panel comic book."""
    
    try:
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating story: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate story: {str(e)}")

def break_story_into_panels(story, num_panels=10):
    """Break down the story into specified number of panels"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": f"Break down this story into exactly {num_panels} sequential panels for a comic book. For each panel, provide: 1) A description of what should be shown in the image, and 2) The text/dialogue that should appear in the panel. Format as JSON array with objects containing 'image_description' and 'panel_text' fields."},
                {"role": "user", "content": story}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("panels", [])
    except Exception as e:
        logger.error(f"Error breaking story into panels: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to break story into panels: {str(e)}")

async def generate_pixel_art(description, panel_number, project_id):
    """Generate pixel art using OpenAI DALL-E"""
    prompt = f"Create pixel art for a children's comic: {description}. Use bright colors, simple shapes, and a pixelated style. Make it cute and child-friendly."
    
    try:
        response = await asyncio.to_thread(
            openai_client.images.generate,
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        # Get the image URL
        image_url = response.data[0].url
        
        # Download the image
        import requests
        image_data = requests.get(image_url).content
        
        # Save the image
        images_dir = STORAGE_DIR / project_id / "images"
        image_path = images_dir / f"panel_{panel_number}.png"
        
        with open(image_path, "wb") as f:
            f.write(image_data)
        
        return str(image_path)
    except Exception as e:
        logger.error(f"Error generating pixel art: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate pixel art: {str(e)}")

def create_comic_page(project_id, panels):
    """Create a comic book by arranging panels and adding text"""
    try:
        images_dir = STORAGE_DIR / project_id / "images"
        output_dir = STORAGE_DIR / project_id / "output"
        comic_path = output_dir / "comic.png"
        
        # Define comic page dimensions
        page_width = 2400
        page_height = 3000
        panel_width = 1100
        panel_height = 500
        
        # Create a blank white canvas
        comic = Image.new('RGB', (page_width, page_height), color='white')
        draw = ImageDraw.Draw(comic)
        
        # Try to load a font, fall back to default if not available
        try:
            font = ImageFont.truetype("Arial.ttf", 32)
            small_font = ImageFont.truetype("Arial.ttf", 24)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Calculate layout (2x5 grid)
        margin = 50
        panels_per_row = 2
        rows = 5
        
        for i, panel in enumerate(panels[:10]):  # Limit to 10 panels
            # Calculate position
            row = i // panels_per_row
            col = i % panels_per_row
            
            x = margin + col * (panel_width + margin)
            y = margin + row * (panel_height + margin + 100)  # Extra space for text
            
            try:
                # Open and resize panel image
                panel_path = images_dir / f"panel_{i+1}.png"
                if panel_path.exists():
                    panel_img = Image.open(panel_path)
                    panel_img = panel_img.resize((panel_width, panel_height), Image.LANCZOS)
                    comic.paste(panel_img, (x, y))
                else:
                    # Create placeholder if image doesn't exist
                    draw.rectangle([x, y, x + panel_width, y + panel_height], outline="black", width=2)
                    draw.text((x + 10, y + panel_height // 2), f"Panel {i+1}", fill="black", font=font)
                
                # Add panel number
                draw.text((x + 5, y - 30), f"Panel {i+1}", fill="black", font=small_font)
                
                # Add text below the panel
                panel_text = panel.get("panel_text", "")
                wrapped_text = textwrap.fill(panel_text, width=50)
                draw.text((x, y + panel_height + 10), wrapped_text, fill="black", font=small_font)
                
            except Exception as e:
                logger.error(f"Error processing panel {i+1}: {str(e)}")
                # Create error placeholder
                draw.rectangle([x, y, x + panel_width, y + panel_height], outline="red", width=2)
                draw.text((x + 10, y + panel_height // 2), f"Error: {str(e)[:20]}", fill="red", font=small_font)
        
        # Add title at the top
        title_y = 10
        draw.text((page_width // 2 - 150, title_y), "My AI Comic Story", fill="black", font=ImageFont.truetype("Arial.ttf", 48) if 'Arial.ttf' in ImageFont.truetype.__code__.co_varnames else ImageFont.load_default())
        
        # Save the comic
        comic.save(comic_path)
        return str(comic_path)
    except Exception as e:
        logger.error(f"Error creating comic: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create comic: {str(e)}")

async def generate_voiceover(story, project_id):
    """Generate voice over for the story using OpenAI"""
    try:
        audio_dir = STORAGE_DIR / project_id / "audio"
        audio_path = audio_dir / "voiceover.mp3"
        
        response = await asyncio.to_thread(
            openai_client.audio.speech.create,
            model="tts-1",
            voice="nova",
            input=story
        )
        
        # Save the audio
        response.stream_to_file(str(audio_path))
        return str(audio_path)
    except Exception as e:
        logger.error(f"Error generating voiceover: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate voiceover: {str(e)}")

def create_final_output(project_id):
    """Create the final output by combining comic and audio (returns paths to both)"""
    try:
        comic_path = STORAGE_DIR / project_id / "output" / "comic.png"
        audio_path = STORAGE_DIR / project_id / "audio" / "voiceover.mp3"
        
        # In a full implementation, you might create a video using ffmpeg
        # For now, we'll return paths to both files
        
        return str(comic_path), str(audio_path)
    except Exception as e:
        logger.error(f"Error creating final output: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create final output: {str(e)}")

# API Endpoints
@app.post("/generate-comic", response_model=ComicProgress)
async def start_comic_generation(story_prompt: StoryPrompt, background_tasks: BackgroundTasks):
    """Start comic generation process"""
    project_id = str(uuid.uuid4())
    create_project_dirs(project_id)
    
    # Initialize progress
    update_progress(project_id, "started", 0, 6, "Starting comic generation...")
    
    # Start background task
    background_tasks.add_task(process_comic_generation, project_id, story_prompt)
    
    return ComicProgress(**job_progress[project_id])

async def process_comic_generation(project_id: str, story_prompt: StoryPrompt):
    """Process comic generation in background"""
    try:
        # Step 1: Generate story
        update_progress(project_id, "generating_story", 1, 6, "Generating story...")
        story = await generate_story(story_prompt.prompt, story_prompt.style, story_prompt.character_names)
        
        # Step 2: Break story into panels
        update_progress(project_id, "breaking_story", 2, 6, "Breaking story into panels...", story=story)
        panels = break_story_into_panels(story, story_prompt.num_panels)
        
        # Step 3: Generate pixel art for each panel
        update_progress(project_id, "generating_images", 3, 6, "Generating panel images...", story=story, panels=panels)
        for i, panel in enumerate(panels):
            panel_path = await generate_pixel_art(panel["image_description"], i+1, project_id)
            panels[i]["image_path"] = panel_path
            # Update progress for each panel
            update_progress(
                project_id, 
                "generating_images", 
                3, 6, 
                f"Generated image {i+1} of {len(panels)}...",
                story=story, 
                panels=panels
            )
        
        # Step 4: Create comic book
        update_progress(project_id, "creating_comic", 4, 6, "Creating comic book...", story=story, panels=panels)
        comic_path = create_comic_page(project_id, panels)
        
        # Step 5: Generate voice over
        update_progress(
            project_id, 
            "generating_audio", 
            5, 6, 
            "Generating voice over...",
            story=story, 
            panels=panels, 
            comic_url=f"/files/{project_id}/output/comic.png"
        )
        audio_path = await generate_voiceover(story, project_id)
        
        # Step 6: Create final output
        update_progress(
            project_id, 
            "finalizing", 
            6, 6, 
            "Creating final output...",
            story=story, 
            panels=panels, 
            comic_url=f"/files/{project_id}/output/comic.png",
            audio_url=f"/files/{project_id}/audio/voiceover.mp3"
        )
        comic_path, audio_path = create_final_output(project_id)
        
        # Update with completion status
        update_progress(
            project_id, 
            "completed", 
            6, 6, 
            "Comic generation completed!",
            story=story, 
            panels=panels, 
            comic_url=f"/files/{project_id}/output/comic.png",
            audio_url=f"/files/{project_id}/audio/voiceover.mp3",
            final_url=f"/files/{project_id}/output/comic.png"  # Same as comic_url for now
        )
        
    except Exception as e:
        logger.error(f"Error in comic generation process: {str(e)}")
        update_progress(project_id, "error", 0, 6, f"Error: {str(e)}")

@app.get("/status/{project_id}", response_model=ComicProgress)
async def check_status(project_id: str):
    """Check the status of comic generation"""
    if project_id not in job_progress:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return ComicProgress(**job_progress[project_id])

@app.get("/files/{project_id}/{file_type}/{filename}")
async def get_file(project_id: str, file_type: str, filename: str):
    """Serve generated files"""
    file_path = STORAGE_DIR / project_id / file_type / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(str(file_path))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
