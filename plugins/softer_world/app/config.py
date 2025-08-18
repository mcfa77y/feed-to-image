"""
Configuration settings for the Flask application.
"""

import os


class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = False
    TESTING = False
    
    # Image generation settings
    DEFAULT_IMAGE_WIDTH = 600
    DEFAULT_IMAGE_HEIGHT = 448
    FOOTER_MARGIN_PIXELS = 10
    COMIC_BOTTOM_MARGIN = 100
    QR_CODE_SIZE = 2
    QR_CODE_BORDER = 2
    QR_CODE_BOTTOM_OFFSET = 20
    DEFAULT_FONT_SIZE = 18
    DEFAULT_LINE_SPACING = 1.1
    
    # Output settings
    OUTPUT_DIRECTORY = "build"
    
    # API Keys
    OPENWEATHERMAP_API_KEY = os.environ.get('OPENWEATHERMAP_API_KEY') or '805bdda8dde4ad3384006509982278d7'


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
