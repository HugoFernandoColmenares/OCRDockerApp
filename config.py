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

DEV_SECRET_KEY = 'dev-secret-key-change-in-production'

# Application configuration
class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', DEV_SECRET_KEY)
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    APP_PASSWORD = os.environ.get('APP_PASSWORD', '')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'data' / 'inventory.db'))
    MAX_STORED_UPLOADS = int(os.environ.get('MAX_STORED_UPLOADS', '100'))
    UPLOAD_MAX_AGE_DAYS = int(os.environ.get('UPLOAD_MAX_AGE_DAYS', '7'))
    
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
    CORS_ORIGINS = [
        origin.strip()
        for origin in os.environ.get(
            'CORS_ORIGINS', 'http://localhost,http://localhost:8000'
        ).split(',')
        if origin.strip()
    ]

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


def validate_runtime(cfg):
    """Refuse a production process that still has the development secret or no operator password."""
    if getattr(cfg, 'DEBUG', False) or getattr(cfg, 'TESTING', False):
        return
    if not cfg.SECRET_KEY or cfg.SECRET_KEY == DEV_SECRET_KEY:
        raise RuntimeError(
            'SECRET_KEY must be set to a non-default value when FLASK_ENV=production'
        )
    if not cfg.APP_PASSWORD:
        raise RuntimeError('APP_PASSWORD must be set when FLASK_ENV=production')