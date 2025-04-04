import os
import secrets

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}
    
    # Server configuration
    USE_HTTPS = os.environ.get('USE_HTTPS', 'false').lower() == 'true'
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
    SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    
    # Trash bin configuration
    TRASH_ENABLED = True
    DEFAULT_TRASH_RETENTION_DAYS = 30
    AUTO_CLEAN_TRASH = True
    
    # Transfer rate monitoring
    MONITOR_TRANSFER_SPEED = True
    
    # Upload configuration
    ALLOW_FOLDER_UPLOAD = True

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dev.db')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test.db')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prod.db')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 