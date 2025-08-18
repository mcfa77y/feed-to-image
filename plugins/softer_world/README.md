# Softer World Generator

A Python application that generates Softer World comic images with weather integration.

## Features

- Generate random or specific Softer World comic images
- Fetch weather data from wttr.in for any zipcode
- Flask web server with REST API endpoints
- Modular architecture with shared utilities

## Installation

This project uses `uv` for dependency management:

```bash
# Install dependencies
uv sync

# Run the server
uv run python run.py
```

## API Endpoints

- `GET /` - Health check
- `GET /comic` - Generate random comic
- `GET /comic/<number>` - Generate specific comic
- `GET /comic/<number>/<dimensions>` - Generate comic with custom dimensions

## Usage

```python
from weather_generator import fetch_weather_image
from comic_generator import fetch_comic_metadata

# Get weather image for zipcode
weather_img = fetch_weather_image("94110")

# Get comic metadata
comic_data = fetch_comic_metadata(100)
```
