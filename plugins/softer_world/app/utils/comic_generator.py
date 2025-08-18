"""
Softer World Comic Generator Module

This module contains the core functions for generating Softer World comic images.
Extracted from __main__.py to be reusable by the server.
"""

import logging
import math
import random
import sys
from typing import Optional, Tuple

import qrcode
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from font_roboto import Roboto

# Import shared utilities
from app.utils.generator_utils import (
    download_image_from_url,
    calculate_image_dimensions,
    render_text_in_rectangle
)

# Configuration constants
DEFAULT_IMAGE_WIDTH = 600
DEFAULT_IMAGE_HEIGHT = 448
FOOTER_MARGIN_PIXELS = 10
OUTPUT_DIRECTORY = "build"
DEFAULT_FONT_SIZE = 18
COMIC_BOTTOM_MARGIN = 100
QR_CODE_SIZE = 2
QR_CODE_BORDER = 2
QR_CODE_BOTTOM_OFFSET = 20
DEFAULT_LINE_SPACING = 1.1

# Initialize font and dimensions
default_font = ImageFont.truetype(Roboto, DEFAULT_FONT_SIZE)




def create_comic_url(comic_number: Optional[int] = None) -> str:
    if comic_number is not None:        
        return f"https://www.asofterworld.com/index.php?id={comic_number}"
    else:
        # random number between 1 and 1242
        comic_number = random.randint(1, 1242)
        return f"https://www.asofterworld.com/index.php?id={comic_number}"

def fetch_comic_metadata(comic_number: Optional[int] = None) -> dict:
    """
    Fetch comic metadata from the HTML page.
    
    Args:
        comic_number: Specific comic number, or None for random
        
    Returns:
        Dictionary containing comic metadata
    """
    comic_url = create_comic_url(comic_number)
    
    try:
        response = requests.get(comic_url)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract comic image and metadata
        comic_img_element = soup.select_one('#comicimg > img')
        if not comic_img_element:
            raise ValueError("Could not find comic image element")
        
        img_src = comic_img_element.get('src')
        title = comic_img_element.get('title', '')
        
        # Extract comic number from URL or use the passed/generated one
        if comic_number is None:
            # Extract from URL if it was randomly generated
            import re
            match = re.search(r'id=(\d+)', comic_url)
            comic_num = int(match.group(1)) if match else None
        else:
            comic_num = comic_number
        
        return {
            'img': img_src,
            'title': title,
            'num': comic_num,
            'alt': title,  # Using title as alt text as specified
            'url': comic_url
        }
        
    except requests.RequestException as error:
        print(f"Error fetching comic data: {error}")
        raise
    except Exception as error:
        print(f"Error parsing comic metadata: {error}")
        raise






def create_qr_code(comic_url: str) -> Image.Image:
    """
    Generate a QR code for the comic URL.
    
    Args:
        comic_url: URL to encode in QR code
        
    Returns:
        PIL Image of the QR code
    """
    qr_generator = qrcode.QRCode(
        version=1,
        box_size=QR_CODE_SIZE,
        border=QR_CODE_BORDER
    )
    qr_generator.add_data(comic_url)
    qr_generator.make(fit=True)
    
    return qr_generator.make_image(fill_color="black", back_color="white").get_image()



def generate_filename_suffix(comic_metadata: dict, canvas_width: int, canvas_height: int) -> str:
    """
    Generate appropriate filename suffix based on comic and dimensions.
    
    Args:
        comic_metadata: Comic metadata dictionary
        canvas_width: Canvas width
        canvas_height: Canvas height
        
    Returns:
        Filename suffix string
    """
    # Use comic number if available, otherwise "daily"
    comic_identifier = str(comic_metadata.get("num", "daily"))
    
    # Add dimensions if different from default
    dimension_suffix = ""
    if (canvas_width, canvas_height) != (DEFAULT_IMAGE_WIDTH, DEFAULT_IMAGE_HEIGHT):
        dimension_suffix = f"-{canvas_width}x{canvas_height}"
    
    return f"{dimension_suffix}-{comic_identifier}"
