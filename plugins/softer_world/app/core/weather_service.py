"""
Weather service layer for handling weather-related operations.
"""

import io
from typing import IO
from typing import Optional

from PIL import Image

from app.utils.weather_generator import fetch_weather_image


class WeatherService:
    """Service class for weather operations."""
    
    def get_weather_image(self, zipcode: str, view_option: str = "0", 
                         add_frame: bool = True, width: Optional[int] = None, 
                         height: Optional[int] = None) -> Image.Image:
        """
        Get weather image as PIL Image.
        
        Args:
            zipcode: US zipcode (e.g., "94110")
            view_option: Weather view option - "0" (current), "1" (today), "2" (today+tomorrow)
            add_frame: Whether to add a frame around the output
            width: Optional target width for scaling
            height: Optional target height for scaling
            
        Returns:
            PIL Image object of the weather
        """
        return fetch_weather_image(zipcode, view_option, add_frame, width, height)
    
    def get_weather_image_as_bytes(self, zipcode: str, view_option: str = "0", 
                                  add_frame: bool = True, width: Optional[int] = None,
                                  height: Optional[int] = None) -> io.BytesIO:
        """
        Get weather image as BytesIO for HTTP response.
        
        Args:
            zipcode: US zipcode (e.g., "94110")
            view_option: Weather view option - "0" (current), "1" (today), "2" (today+tomorrow)
            add_frame: Whether to add a frame around the output
            width: Optional target width for scaling
            height: Optional target height for scaling
            
        Returns:
            BytesIO object containing the weather image
        """
        weather_image = self.get_weather_image(zipcode, view_option, add_frame, width, height)
        
        # Convert to BytesIO
        img_io = io.BytesIO()
        weather_image.save(img_io, 'JPEG')
        img_io.seek(0)
        
        return img_io
