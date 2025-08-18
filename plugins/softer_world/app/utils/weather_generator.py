"""
Weather Generator Module

This module contains functions for fetching and processing weather data.
"""

import io
import logging
from typing import Optional

import requests
from PIL import Image


def fetch_weather_image(zipcode: str, view_option: str = "0", add_frame: bool = True, 
                       width: Optional[int] = None, height: Optional[int] = None) -> Image.Image:
    """
    Fetch weather PNG image from wttr.in for a given zipcode using metric units.
    
    Args:
        zipcode: US zipcode (e.g., "94110")
        view_option: Weather view option - "0" (current only), "1" (today), "2" (today+tomorrow)
        add_frame: Whether to add a frame around the output
        width: Optional target width for scaling
        height: Optional target height for scaling
        
    Returns:
        PIL Image object of the weather PNG
        
    Raises:
        requests.RequestException: If the request fails
        ValueError: If the image cannot be loaded
    """
    logger = logging.getLogger(__name__)
    
    # Build PNG options string
    png_options = f"{view_option}q"  # view option + quiet (no "Weather report" text)
    if add_frame:
        png_options += "p"  # add frame
    
    # wttr.in URL for PNG weather image with metric units and options
    weather_url = f"https://wttr.in/{zipcode}_{png_options}.png?m"
    
    logger.debug(f"Fetching weather image from: {weather_url}")
    
    try:
        response = requests.get(weather_url)
        response.raise_for_status()
        
        weather_image = Image.open(io.BytesIO(response.content))
        logger.info(f"Successfully fetched weather image for zipcode {zipcode}")
        logger.debug(f"Weather image dimensions: {weather_image.size}")
        
        # Convert PNG to JPEG format
        if weather_image.mode in ("RGBA", "P"):
            # Convert to RGB for JPEG compatibility
            weather_image = weather_image.convert("RGB")
        
        # Scale image if dimensions are provided
        if width is not None and height is not None:
            weather_image = weather_image.resize((width, height), Image.Resampling.LANCZOS)
            logger.debug(f"Scaled weather image to {width}x{height}")
        
        return weather_image
        
    except requests.RequestException as error:
        logger.error(f"Error fetching weather image for {zipcode}: {error}")
        raise
    except Exception as error:
        logger.error(f"Error processing weather image for {zipcode}: {error}")
        raise ValueError(f"Could not load weather image: {error}")
