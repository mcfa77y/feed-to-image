"""
Generator Utilities Module

This module contains common utility functions shared across different generators.
"""

import io
import logging
import math
from typing import Tuple, Optional

import requests
from PIL import Image, ImageDraw, ImageFont


def download_image_from_url(image_url: str) -> Image.Image:
    """
    Download and open an image from URL.
    
    Args:
        image_url: URL of the image
        
    Returns:
        PIL Image object
        
    Raises:
        requests.RequestException: If the request fails
        ValueError: If the image cannot be loaded
    """
    logger = logging.getLogger(__name__)
    logger.debug(f"Downloading image from: {image_url}")
    
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        
        image = Image.open(io.BytesIO(response.content))
        logger.debug(f"Downloaded image dimensions: {image.size}")
        return image
        
    except requests.RequestException as error:
        logger.error(f"Error downloading image: {error}")
        raise
    except Exception as error:
        logger.error(f"Error processing image: {error}")
        raise ValueError(f"Could not load image: {error}")


def calculate_image_dimensions(original_image: Image.Image, canvas_width: int, canvas_height: int, 
                             bottom_margin: int = 0) -> Tuple[int, int, int, int]:
    """
    Calculate the dimensions and position for an image on a canvas.
    
    Args:
        original_image: The original image
        canvas_width: Target canvas width
        canvas_height: Target canvas height
        bottom_margin: Bottom margin to reserve (default: 0)
        
    Returns:
        Tuple of (resized_width, resized_height, offset_x, offset_y)
    """
    logger = logging.getLogger(__name__)
    
    original_width, original_height = original_image.size
    available_height = canvas_height - bottom_margin
    
    logger.debug(f"Original image dimensions: {original_width}x{original_height}")
    logger.debug(f"Canvas dimensions: {canvas_width}x{canvas_height}")
    logger.debug(f"Available height (after margin): {available_height}")
    
    # Calculate scaling ratio to fit image within available space
    width_ratio = canvas_width / original_width
    height_ratio = available_height / original_height
    scaling_ratio = min(width_ratio, height_ratio)  # Don't upscale
    
    logger.debug(f"Scaling ratios - width: {width_ratio:.3f}, height: {height_ratio:.3f}")
    logger.debug(f"Selected scaling ratio: {scaling_ratio:.3f}")
    
    # Calculate new dimensions
    new_width = int(original_width * scaling_ratio)
    new_height = int(original_height * scaling_ratio)
    
    logger.debug(f"Resized dimensions: {new_width}x{new_height}")
    
    # Center the image
    offset_x = int((canvas_width - new_width) / 2)
    offset_y = int((available_height - new_height) / 2)
    
    logger.info(f"Image positioned at ({offset_x}, {offset_y}) with size {new_width}x{new_height}")
    
    return new_width, new_height, offset_x, offset_y


def render_text_in_rectangle(
    canvas: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont,
    text_color: Tuple[int, int, int],
    rectangle_bounds: Tuple[int, int, int, int],
    horizontal_alignment: str = 'left',
    vertical_alignment: str = 'top',
    line_spacing_multiplier: float = 1.1
) -> Optional[Tuple[int, int, int, int]]:
    """
    Render text within a specified rectangle, automatically scaling font size to fit.
    
    Args:
        canvas: PIL ImageDraw object to draw on
        text: Text content to render
        font: Font object to use for rendering
        text_color: RGB color tuple for text
        rectangle_bounds: (left, top, right, bottom) rectangle coordinates
        horizontal_alignment: 'left' or 'center' text alignment
        vertical_alignment: 'top' or 'center' text alignment
        line_spacing_multiplier: Multiplier for line height spacing
        
    Returns:
        Tuple of actual text bounds (left, top, right, bottom) or None if text doesn't fit
    """
    rect_width = rectangle_bounds[2] - rectangle_bounds[0]
    rect_height = rectangle_bounds[3] - rectangle_bounds[1]

    # Iteratively reduce font size until text fits in rectangle
    current_font = font
    while current_font.size > 0:
        line_height = int(current_font.size * line_spacing_multiplier)
        max_lines_possible = math.floor(rect_height / line_height)
        text_lines = []

        # Break text into lines that fit within the rectangle width
        remaining_words = text.split(" ")

        while len(text_lines) < max_lines_possible and len(remaining_words) > 0:
            current_line_words = []

            # Add words to current line until width limit is reached
            while (len(remaining_words) > 0 and 
                   current_font.getbbox(" ".join(current_line_words + [remaining_words[0]]))[2] <= rect_width):
                current_line_words.append(remaining_words.pop(0))

            if current_line_words:  # Only add non-empty lines
                text_lines.append(" ".join(current_line_words))
            else:
                break  # Word too long for line, need smaller font

        # Check if all text fits
        if len(text_lines) <= max_lines_possible and len(remaining_words) == 0:
            # Calculate starting Y position based on vertical alignment
            if vertical_alignment == 'top':
                start_y = int(rectangle_bounds[1])
            else:  # center alignment
                total_text_height = len(text_lines) * line_height
                start_y = int(rectangle_bounds[1] + (rect_height / 2) - (total_text_height / 2) - (line_height - current_font.size) / 2)

            # Track actual text bounds
            text_bounds = [rectangle_bounds[2], int(start_y), rectangle_bounds[0], int(start_y + len(text_lines) * line_height)]

            # Render each line
            current_y = start_y
            for line_text in text_lines:
                line_width = current_font.getbbox(line_text)[2]
                
                # Calculate X position based on horizontal alignment
                if horizontal_alignment == 'center':
                    line_x = int(rectangle_bounds[0] + (rect_width / 2) - (line_width / 2))
                else:  # left alignment
                    line_x = rectangle_bounds[0]
                    
                # Update bounds tracking
                text_bounds[0] = min(text_bounds[0], int(line_x))
                text_bounds[2] = max(text_bounds[2], int(line_x + line_width))
                
                # Draw the line
                canvas.text((line_x, current_y), line_text, text_color, font=current_font)
                current_y += line_height

            return (text_bounds[0], text_bounds[1], text_bounds[2], text_bounds[3])

        # Try smaller font size
        current_font = ImageFont.truetype(current_font.path, current_font.size - 1)
    
    return None  # Text doesn't fit even at smallest font size


def generate_filename_suffix(metadata: dict, canvas_width: int, canvas_height: int, 
                           default_width: int, default_height: int) -> str:
    """
    Generate appropriate filename suffix based on metadata and dimensions.
    
    Args:
        metadata: Metadata dictionary
        canvas_width: Canvas width
        canvas_height: Canvas height
        default_width: Default canvas width
        default_height: Default canvas height
        
    Returns:
        Filename suffix string
    """
    # Use identifier if available, otherwise "daily"
    identifier = str(metadata.get("num", metadata.get("id", "daily")))
    
    # Add dimensions if different from default
    dimension_suffix = ""
    if (canvas_width, canvas_height) != (default_width, default_height):
        dimension_suffix = f"-{canvas_width}x{canvas_height}"
    
    return f"{dimension_suffix}-{identifier}"
