"""Image processing service for comic generation."""
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from loguru import logger
import base64
import textwrap

class ImageService:
    """Service for handling image processing operations."""
    
    @staticmethod
    def create_comic_page(
        images: List[bytes],
        panel_texts: List[str],
        output_path: Path,
        page_width: int = 2400,
        page_height: int = 3000,
        panel_width: int = 1100,
        panel_height: int = 500
    ) -> Path:
        """Create a comic page by arranging panels and adding text.
        
        Args:
            images: List of image bytes for each panel
            panel_texts: List of text for each panel
            output_path: Path to save the comic page
            page_width: Width of the comic page
            page_height: Height of the comic page
            panel_width: Width of each panel
            panel_height: Height of each panel
            
        Returns:
            Path to the saved comic page
        """
        try:
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
            
            # Calculate layout
            margin = 50
            y_offset = margin
            
            for i, (img_data, text) in enumerate(zip(images, panel_texts)):
                # Open and resize the image
                img = Image.open(BytesIO(img_data))
                img = img.resize((panel_width, panel_height), Image.Resampling.LANCZOS)
                
                # Calculate position (center the panel)
                x = (page_width - panel_width) // 2
                
                # Add panel number
                draw.text((x, y_offset - 30), f"Panel {i+1}", fill="black", font=small_font)
                
                # Paste the image
                comic.paste(img, (x, y_offset))
                
                # Add text below the image
                y_text = y_offset + panel_height + 10
                
                # Wrap text to fit panel width
                wrapped_text = textwrap.fill(text, width=50)
                
                # Draw text with a slight shadow for better visibility
                draw.text((x, y_text + 2), wrapped_text, fill="black", font=font)
                draw.text((x, y_text), wrapped_text, fill="white", font=font)
                
                # Update y-offset for next panel
                y_offset = y_text + 100  # Adjust based on text height
                
                # Add some space between panels
                if i < len(images) - 1:
                    y_offset += 30
            
            # Save the final comic
            comic.save(output_path, "PNG")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating comic page: {str(e)}")
            raise
    
    @staticmethod
    def combine_images_vertically(images: List[bytes], output_path: Path) -> Path:
        """Combine multiple images vertically.
        
        Args:
            images: List of image bytes to combine
            output_path: Path to save the combined image
            
        Returns:
            Path to the combined image
        """
        try:
            # Open all images
            pil_images = [Image.open(BytesIO(img)) for img in images]
            
            # Calculate total height and max width
            widths, heights = zip(*(i.size for i in pil_images))
            total_height = sum(heights)
            max_width = max(widths)
            
            # Create a new image with the right dimensions
            combined = Image.new('RGB', (max_width, total_height))
            
            # Paste images one below the other
            y_offset = 0
            for img in pil_images:
                combined.paste(img, (0, y_offset))
                y_offset += img.height
            
            # Save the combined image
            combined.save(output_path, "PNG")
            return output_path
            
        except Exception as e:
            logger.error(f"Error combining images: {str(e)}")
            raise
