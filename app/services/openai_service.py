"""OpenAI service for generating comic content."""
import json
import asyncio
from typing import List, Optional, Dict, Any
import openai
from loguru import logger
from jinja2 import Template
from app.config import settings
from app.models.comic_models import Panel, ComicStatus
import base64

# client = OpenAI()
# Configure OpenAI client
openai.api_key = settings.OPENAI_API_KEY

class OpenAIService:
    """Service for handling OpenAI API interactions."""
    
    @staticmethod
    async def generate_story(
        prompt: str, 
        style: str = "child-friendly fantasy", 
        character_names: Optional[List[str]] = None,
        num_panels: int = 3
    ) -> str:
        """Generate a short story using OpenAI.
        
        Args:
            prompt: The main prompt for the story
            style: Style of the story
            character_names: Optional list of character names to include
            num_panels: Number of panels for the comic book
            
        Returns:
            Generated story text
        """
        character_prompt = f"Include these characters: {', '.join(character_names)}. " if character_names else ""
        
        system_prompt = Template("""Create a short, engaging children's story in the style of {{style}}. 
        The story should be appropriate for children, with a clear beginning, middle, and end.
        {{character_prompt}}
        Keep it concise yet engaging, suitable for a {{num_panels}} panel comic book.""")
        
        system_prompt = system_prompt.render(
            style=style,
            character_prompt=character_prompt,
            num_panels=num_panels
        )
        
        try:
            response = await asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating story: {str(e)}")
            raise
    
    @staticmethod
    def break_story_into_panels(story: str, num_panels: int = 3) -> List[Dict[str, Any]]:
        """Break down the story into specified number of panels."""
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": Template("""Break down this story into exactly {{num_panels}} sequential panels for a comic book. 
                        For each panel, provide: 1) A description of what should be shown in the image, and 
                        2) The text/dialogue that should appear in the panel. 
                        Format as JSON array with objects containing 'image_description' and 'panel_text' fields.
                        Example:
                        ```json
                        {
                            "panels": [
                                {
                                    "image_description": "Description of the image",
                                    "panel_text": "Text for the panel"
                                }
                            ]
                        }
                        ```
                        """).render(num_panels=num_panels)
                    },
                    {"role": "user", "content": story}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("panels", [])
        except Exception as e:
            logger.error(f"Error breaking story into panels: {str(e)}")
            raise
    
    @staticmethod
    async def generate_pixel_art(description: str) -> bytes:
        """Generate pixel art using OpenAI DALL-E."""
        prompt = f"""Create pixel art for a children's comic: {description}. 
        Use bright colors, simple shapes, and a pixelated style. 
        Make it cute and child-friendly."""
        
        try:
            response = await asyncio.to_thread(
                openai.images.generate,
                model="gpt-image-1",
                prompt=prompt
            )
            
            # result = client.images.generate(
            #     model="gpt-image-1",
            #     prompt=prompt
            # )

            image_base64 = response.data[0].b64_json
            image_bytes = base64.b64decode(image_base64)
            return image_bytes
        except Exception as e:
            logger.error(f"Error generating pixel art: {str(e)}")
            raise
    
    @staticmethod
    async def generate_voiceover(text: str) -> bytes:
        """Generate voice over for the story using OpenAI's TTS."""
        try:
            response = await asyncio.to_thread(
                openai.audio.speech.create,
                model="tts-1",
                voice="alloy",
                input=text
            )
            return response.content
        except Exception as e:
            logger.error(f"Error generating voiceover: {str(e)}")
            raise
