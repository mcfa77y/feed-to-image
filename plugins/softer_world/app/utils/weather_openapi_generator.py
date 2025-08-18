"""
Weather OpenAPI Generator Module

This module creates Apple Weather-style weather images using OpenWeatherMap API.
"""

import io
import logging
import math
import requests
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
from app.config import Config


class WeatherOpenAPIGenerator:
    """Generate Apple Weather-style weather images using OpenWeatherMap API."""
    
    def __init__(self):
        self.api_key = Config.OPENWEATHERMAP_API_KEY
        self.logger = logging.getLogger(__name__)
        
        # Apple Weather-style colors
        self.colors = {
            'background': '#1E3A8A',  # Deep blue
            'gradient_top': '#3B82F6',  # Blue
            'gradient_bottom': '#1E40AF',  # Darker blue
            'text_primary': '#FFFFFF',
            'text_secondary': '#E5E7EB',
            'text_muted': '#9CA3AF',
            'card_bg': 'rgba(255, 255, 255, 0.1)',
            'card_border': 'rgba(255, 255, 255, 0.2)',
        }
        
    def get_coordinates_from_zipcode(self, zipcode: str) -> tuple[float, float]:
        """Convert US zipcode to lat/lon coordinates using OpenWeatherMap Geocoding API."""
        geocoding_url = f"http://api.openweathermap.org/geo/1.0/zip"
        params = {
            'zip': f"{zipcode},US",
            'appid': self.api_key
        }
        
        try:
            response = requests.get(geocoding_url, params=params)
            response.raise_for_status()
            data = response.json()
            return data['lat'], data['lon']
        except Exception as e:
            self.logger.error(f"Error getting coordinates for zipcode {zipcode}: {e}")
            raise ValueError(f"Could not get coordinates for zipcode {zipcode}")
    
    def fetch_weather_data(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch weather data from OpenWeatherMap One Call API."""
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            'lat': lat,
            'lon': lon,
            'exclude': 'minutely,alerts',
            'appid': self.api_key,
            'units': 'imperial'  # Fahrenheit for US
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Error fetching weather data: {e}")
            raise ValueError(f"Could not fetch weather data: {e}")
    
    def get_weather_icon_symbol(self, icon_code: str) -> str:
        """Convert OpenWeatherMap icon code to weather symbol."""
        icon_map = {
            '01d': '☀️', '01n': '🌙',  # clear sky
            '02d': '⛅', '02n': '☁️',  # few clouds
            '03d': '☁️', '03n': '☁️',  # scattered clouds
            '04d': '☁️', '04n': '☁️',  # broken clouds
            '09d': '🌧️', '09n': '🌧️',  # shower rain
            '10d': '🌦️', '10n': '🌧️',  # rain
            '11d': '⛈️', '11n': '⛈️',  # thunderstorm
            '13d': '❄️', '13n': '❄️',  # snow
            '50d': '🌫️', '50n': '🌫️',  # mist
        }
        return icon_map.get(icon_code, '☁️')
    
    def create_gradient_background(self, width: int, height: int) -> Image.Image:
        """Create a gradient background similar to Apple Weather."""
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        # Create vertical gradient
        for y in range(height):
            ratio = y / height
            # Interpolate between top and bottom colors
            r = int(59 + (30 - 59) * ratio)  # 3B82F6 to 1E40AF
            g = int(130 + (64 - 130) * ratio)
            b = int(246 + (175 - 246) * ratio)
            color = (r, g, b)
            draw.line([(0, y), (width, y)], fill=color)
        
        return img
    
    def draw_main_weather(self, draw: ImageDraw.Draw, weather_data: Dict, 
                         width: int, height: int, font_large: ImageFont, 
                         font_medium: ImageFont, font_small: ImageFont):
        """Draw the main weather information (temperature, location, condition)."""
        current = weather_data['current']
        
        # Location (you might want to reverse geocode or use a location service)
        location = "Current Location"  # Placeholder
        temp = f"{int(current['temp'])}°"
        condition = current['weather'][0]['description'].title()
        feels_like = f"Feels like {int(current['feels_like'])}°"
        high_low = f"H:{int(weather_data['daily'][0]['temp']['max'])}° L:{int(weather_data['daily'][0]['temp']['min'])}°"
        
        # Draw location
        location_bbox = draw.textbbox((0, 0), location, font=font_medium)
        location_width = location_bbox[2] - location_bbox[0]
        draw.text(((width - location_width) // 2, 40), location, 
                 fill=self.colors['text_secondary'], font=font_medium)
        
        # Draw main temperature
        temp_bbox = draw.textbbox((0, 0), temp, font=font_large)
        temp_width = temp_bbox[2] - temp_bbox[0]
        draw.text(((width - temp_width) // 2, 80), temp, 
                 fill=self.colors['text_primary'], font=font_large)
        
        # Draw condition
        condition_bbox = draw.textbbox((0, 0), condition, font=font_medium)
        condition_width = condition_bbox[2] - condition_bbox[0]
        draw.text(((width - condition_width) // 2, 160), condition, 
                 fill=self.colors['text_secondary'], font=font_medium)
        
        # Draw feels like
        feels_bbox = draw.textbbox((0, 0), feels_like, font=font_small)
        feels_width = feels_bbox[2] - feels_bbox[0]
        draw.text(((width - feels_width) // 2, 190), feels_like, 
                 fill=self.colors['text_muted'], font=font_small)
        
        # Draw high/low
        hl_bbox = draw.textbbox((0, 0), high_low, font=font_small)
        hl_width = hl_bbox[2] - hl_bbox[0]
        draw.text(((width - hl_width) // 2, 210), high_low, 
                 fill=self.colors['text_muted'], font=font_small)
    
    def draw_hourly_forecast(self, draw: ImageDraw.Draw, weather_data: Dict,
                           width: int, y_start: int, font_small: ImageFont):
        """Draw hourly forecast similar to Apple Weather."""
        hourly_data = weather_data['hourly'][:12]  # Next 12 hours
        
        # Card background
        card_height = 120
        draw.rounded_rectangle(
            [(20, y_start), (width - 20, y_start + card_height)],
            radius=15, fill=(255, 255, 255, 25), outline=(255, 255, 255, 50)
        )
        
        # Title
        draw.text((35, y_start + 15), "HOURLY FORECAST", 
                 fill=self.colors['text_muted'], font=font_small)
        
        # Hourly items
        item_width = (width - 60) // 6  # Show 6 hours
        for i, hour_data in enumerate(hourly_data[:6]):
            x = 35 + i * item_width
            
            # Time
            dt = datetime.fromtimestamp(hour_data['dt'], tz=timezone.utc)
            time_str = dt.strftime("%H")
            if i == 0:
                time_str = "Now"
            
            # Center time text
            time_bbox = draw.textbbox((0, 0), time_str, font=font_small)
            time_width = time_bbox[2] - time_bbox[0]
            draw.text((x + (item_width - time_width) // 2, y_start + 35), 
                     time_str, fill=self.colors['text_secondary'], font=font_small)
            
            # Weather icon (simplified)
            icon = self.get_weather_icon_symbol(hour_data['weather'][0]['icon'])
            icon_bbox = draw.textbbox((0, 0), icon, font=font_small)
            icon_width = icon_bbox[2] - icon_bbox[0]
            draw.text((x + (item_width - icon_width) // 2, y_start + 55), 
                     icon, font=font_small)
            
            # Temperature
            temp_str = f"{int(hour_data['temp'])}°"
            temp_bbox = draw.textbbox((0, 0), temp_str, font=font_small)
            temp_width = temp_bbox[2] - temp_bbox[0]
            draw.text((x + (item_width - temp_width) // 2, y_start + 85), 
                     temp_str, fill=self.colors['text_primary'], font=font_small)
    
    def draw_daily_forecast(self, draw: ImageDraw.Draw, weather_data: Dict,
                          width: int, y_start: int, font_small: ImageFont):
        """Draw 7-day forecast."""
        daily_data = weather_data['daily'][:7]
        
        # Card background
        card_height = 200
        draw.rounded_rectangle(
            [(20, y_start), (width - 20, y_start + card_height)],
            radius=15, fill=(255, 255, 255, 25), outline=(255, 255, 255, 50)
        )
        
        # Title
        draw.text((35, y_start + 15), "7-DAY FORECAST", 
                 fill=self.colors['text_muted'], font=font_small)
        
        # Daily items
        for i, day_data in enumerate(daily_data):
            y = y_start + 40 + i * 22
            
            # Day name
            dt = datetime.fromtimestamp(day_data['dt'], tz=timezone.utc)
            day_name = dt.strftime("%a") if i > 0 else "Today"
            draw.text((35, y), day_name, fill=self.colors['text_secondary'], font=font_small)
            
            # Weather icon
            icon = self.get_weather_icon_symbol(day_data['weather'][0]['icon'])
            draw.text((120, y), icon, font=font_small)
            
            # High/Low temps
            high = f"{int(day_data['temp']['max'])}°"
            low = f"{int(day_data['temp']['min'])}°"
            
            # Right align temperatures
            high_bbox = draw.textbbox((0, 0), high, font=font_small)
            high_width = high_bbox[2] - high_bbox[0]
            draw.text((width - 80 - high_width, y), high, 
                     fill=self.colors['text_primary'], font=font_small)
            
            low_bbox = draw.textbbox((0, 0), low, font=font_small)
            low_width = low_bbox[2] - low_bbox[0]
            draw.text((width - 40 - low_width, y), low, 
                     fill=self.colors['text_muted'], font=font_small)
    
    def generate_weather_image(self, zipcode: str, width: int = 400, 
                             height: int = 600) -> Image.Image:
        """Generate Apple Weather-style weather image."""
        try:
            # Get coordinates and weather data
            lat, lon = self.get_coordinates_from_zipcode(zipcode)
            weather_data = self.fetch_weather_data(lat, lon)
            
            # Create base image with gradient
            img = self.create_gradient_background(width, height)
            draw = ImageDraw.Draw(img, 'RGBA')
            
            # Load fonts (fallback to default if not available)
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
                font_medium = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
                font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw main weather info
            self.draw_main_weather(draw, weather_data, width, height, 
                                 font_large, font_medium, font_small)
            
            # Draw hourly forecast
            self.draw_hourly_forecast(draw, weather_data, width, 250, font_small)
            
            # Draw daily forecast
            self.draw_daily_forecast(draw, weather_data, width, 390, font_small)
            
            self.logger.info(f"Successfully generated Apple Weather-style image for zipcode {zipcode}")
            return img
            
        except Exception as e:
            self.logger.error(f"Error generating weather image: {e}")
            raise


def fetch_openapi_weather_image(zipcode: str, width: int = 400, 
                               height: int = 600) -> Image.Image:
    """
    Fetch Apple Weather-style weather image using OpenWeatherMap API.
    
    Args:
        zipcode: US zipcode (e.g., "94110")
        width: Image width in pixels
        height: Image height in pixels
        
    Returns:
        PIL Image object of the Apple Weather-style weather display
        
    Raises:
        ValueError: If the weather data cannot be fetched or processed
    """
    generator = WeatherOpenAPIGenerator()
    return generator.generate_weather_image(zipcode, width, height)
