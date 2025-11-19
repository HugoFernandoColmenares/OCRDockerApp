"""
Configuration module for Inventory OCR Scanner
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
RESULTS_FOLDER = os.environ.get('RESULTS_FOLDER', 'results')

# Create directories if they don't exist
Path(UPLOAD_FOLDER).mkdir(exist_ok=True)
Path(RESULTS_FOLDER).mkdir(exist_ok=True)

# Application configuration
class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    
    # File upload settings
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
    UPLOAD_FOLDER = UPLOAD_FOLDER
    RESULTS_FOLDER = RESULTS_FOLDER
    
    # OCR settings
    TESSERACT_CMD = os.environ.get('TESSERACT_CMD', '/usr/bin/tesseract')
    OCR_LANGUAGE = os.environ.get('OCR_LANGUAGE', 'spa+eng')  # Spanish + English
    OCR_CONFIG = r'--oem 3 --psm 6'
    
    # API settings
    API_TITLE = 'Inventory OCR Scanner API'
    API_VERSION = '1.0.0'
    
    # Security settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Processing settings
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', '4'))
    PROCESSING_TIMEOUT = int(os.environ.get('PROCESSING_TIMEOUT', '60'))
    
    # Logging settings
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    LOG_LEVEL = 'INFO'
    
    # Override secret key for production
    # SECRET_KEY = os.environ.get('SECRET_KEY')
    # if not SECRET_KEY:
    #     pass

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    LOG_LEVEL = 'DEBUG'
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB for testing

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration by name"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    return config.get(config_name, config['default'])