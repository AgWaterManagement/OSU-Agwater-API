import os

class Config:
    """Base configuration with default settings."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_default_secret_key')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paths
    AG_WATER_PATH = os.environ.get('AG_WATER_PATH', 'd:/Websites/AgWaterReact')
    IRRIGATION_DB_PATH = os.environ.get('IRRIGATION_DB_PATH', 'D:/Websites/AgWaterreact/src/pages/IrrigUseNW/Data/IrrigUse.sqlite')

    # Email settings
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'mail.engr.oregonstate.edu')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 25))
    SMTP_USERNAME = os.environ.get('SMTP_USERNAME', 'ag-water')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

class DevelopmentConfig(Config):
    """Development-specific configuration."""
    DEBUG = True
    FLASK_ENV = 'development'
    AG_WATER_PATH = 'd:/Websites/AgWaterReactDev'

class TestingConfig(Config):
    """Testing-specific configuration."""
    TESTING = True
    DEBUG = True
    FLASK_ENV = 'testing'

class ProductionConfig(Config):
    """Production-specific configuration."""
    DEBUG = False
    FLASK_ENV = 'production'

# Map environment names to configuration classes
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

'''
1. Access Configuration in Your Code:
    You can access the configuration values using app.config
    in your routes or services.

from flask import current_app

def get_database_path():
    return current_app.config['IRRIGATION_DB_PATH']

2. Set Environment Variables: Use environment variables
        to override default values in config.py. For example, in a .env
       file or your deployment environment

'''   