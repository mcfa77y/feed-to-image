"""
Comic generation service layer.
"""

import io
from typing import Optional, Tuple

from PIL import Image, ImageDraw
from font_roboto import Roboto
from PIL import ImageFont

from app.config import Config
from app.utils.comic_generator import fetch_comic_metadata, create_qr_code
from app.utils.generator_utils import (
    download_image_from_url,
    calculate_image_dimensions,
    render_text_in_rectangle
)


class ComicService:
    """Service class for comic generation operations."""
    
    def __init__(self):
        self.default_font = ImageFont.truetype(Roboto, Config.DEFAULT_FONT_SIZE)
    
    def fetch_comic_metadata(self, comic_number: Optional[int] = None) -> dict:
        """Fetch comic metadata."""
        return fetch_comic_metadata(comic_number)
    
    def generate_comic_image(self, comic_number: Optional[int] = None, 
                           width: int = None, height: int = None) -> Tuple[io.BytesIO, dict]:
        """
        Generate a Softer World comic image and return it as a BytesIO object.
        
        Args:
            comic_number: Specific comic number, or None for random
            width: Canvas width
            height: Canvas height
            
        Returns:
            Tuple of (BytesIO object containing the generated image, comic metadata)
        """
        if width is None:
            width = Config.DEFAULT_IMAGE_WIDTH
        if height is None:
            height = Config.DEFAULT_IMAGE_HEIGHT
            
        # Fetch comic metadata
        comic_metadata = self.fetch_comic_metadata(comic_number)
        
        # Download comic image
        img_url = comic_metadata.get("img")
        if not img_url:
            raise ValueError("No image URL found in comic metadata")
        comic_image = download_image_from_url(img_url)
        
        # Calculate comic dimensions and position
        comic_width, comic_height, comic_x, comic_y = calculate_image_dimensions(
            comic_image, width, height, Config.COMIC_BOTTOM_MARGIN
        )
        
        # Resize comic if necessary
        if (comic_width, comic_height) != comic_image.size:
            comic_image = comic_image.resize((comic_width, comic_height))
        
        # Create QR code
        comic_url = f"https://www.asofterworld.com/index.php?id={comic_metadata.get('num')}/"
        qr_code_image = create_qr_code(comic_url)
        qr_width, qr_height = qr_code_image.size
        
        # Calculate QR code position (bottom right)
        qr_x = width - qr_width - Config.FOOTER_MARGIN_PIXELS
        qr_y = height - qr_height - Config.FOOTER_MARGIN_PIXELS - Config.QR_CODE_BOTTOM_OFFSET
        
        # Calculate text area (bottom left, next to QR code)
        text_area_x = Config.FOOTER_MARGIN_PIXELS
        text_area_y = qr_y
        text_area_width = qr_x - Config.FOOTER_MARGIN_PIXELS - text_area_x
        text_area_height = qr_height
        
        # Create output canvas
        output_canvas = Image.new("RGB", (width, height), color=(255, 255, 255))
        drawing_context = ImageDraw.Draw(output_canvas)
        
        # Paste comic image
        output_canvas.paste(comic_image, (comic_x, comic_y, comic_x + comic_width, comic_y + comic_height))
        
        # Paste QR code
        output_canvas.paste(qr_code_image, (qr_x, qr_y, qr_x + qr_width, qr_y + qr_height))
        
        # Render alt text
        alt_text = comic_metadata.get("alt", "")
        if alt_text:
            render_text_in_rectangle(
                drawing_context,
                alt_text,
                self.default_font,
                (0, 0, 0),  # Black text
                (text_area_x, text_area_y, text_area_x + text_area_width, text_area_y + text_area_height)
            )
        
        # Render website attribution
        render_text_in_rectangle(
            drawing_context,
            "www.asofterworld.com",
            self.default_font,
            (0, 0, 0),  # Black text
            (qr_x, qr_y + qr_height, qr_x + qr_width, qr_y + qr_height + Config.QR_CODE_BOTTOM_OFFSET)
        )
        
        # Save to BytesIO
        img_io = io.BytesIO()
        output_canvas.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        
        return img_io, comic_metadata
