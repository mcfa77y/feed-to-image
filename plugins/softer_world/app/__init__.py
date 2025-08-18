"""
Softer World Generator Flask Application
"""

import logging
import os
from flask import Flask


def create_app(config_name='default'):
    """Application factory pattern for creating Flask app."""
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create build directory if it doesn't exist
    os.makedirs('build', exist_ok=True)
    
    # Register blueprints
    from app.api.comics import comics_bp
    from app.api.health import health_bp
    from app.api.weather import weather_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(comics_bp, url_prefix='/comic')
    app.register_blueprint(weather_bp, url_prefix='/weather')
    
    return app
