import os
import secrets
import platform
import sys
from pathlib import Path
from flask import Flask

def get_base_storage_path() -> Path:
    """Get the base storage path based on the operating system"""
    system = platform.system().lower()
    if system == 'windows':
        return Path('D:/cloud_storage')
    elif system == 'linux':
        if os.path.exists('/mnt/cloud_storage'):
            return Path('/mnt/cloud_storage')
        return Path.home() / 'cloud_storage'
    elif system == 'darwin':
        return Path.home() / 'cloud_storage'
    else:
        return Path(__file__).parent / 'storage'

def get_storage_path() -> str:
    """Get the uploads storage path"""
    base_path = get_base_storage_path()
    uploads_path = base_path / 'uploads'
    uploads_path.mkdir(parents=True, exist_ok=True)
    return str(uploads_path)

def get_db_path(env: str) -> str:
    """Get the database path based on environment and operating system"""
    base_path = get_base_storage_path()
    if env == 'development':
        db_path = Path(__file__).parent / 'dev.db'
    else:
        db_path = base_path / 'home-cloud' / 'production.db'
    
    # Ensure database directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)

class Config(object):
    # Basic configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(16)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = get_storage_path()
    MAX_CONTENT_LENGTH = 20000 * 1024 * 1024 * 1024  # 20TB max file size
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mp3', 
                         'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar', 'md', 'py', 
                         'js', 'css', 'html', 'json', 'xml'}
    
    # Server configuration
    USE_HTTPS = True
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
    SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    
    # SSL certificate configuration
    system = platform.system().lower()
    if system == 'windows':
        SSL_CERT = str(Path(__file__).parent / 'ssl' / 'home-cloud.crt')
        SSL_KEY = str(Path(__file__).parent / 'ssl' / 'home-cloud.key')
    else:
        SSL_CERT = '/etc/ssl/certs/home-cloud.crt'
        SSL_KEY = '/etc/ssl/private/home-cloud.key'
    
    # Trash bin configuration
    TRASH_ENABLED = True
    DEFAULT_TRASH_RETENTION_DAYS = 30
    AUTO_CLEAN_TRASH = True
    TRASH_PATH = str(get_base_storage_path() / 'trash')
    
    # Transfer rate monitoring
    MONITOR_TRANSFER_SPEED = True
    
    # Upload configuration
    ALLOW_FOLDER_UPLOAD = True
    TEMP_UPLOAD_PATH = str(get_base_storage_path() / 'temp')

    @staticmethod
    def init_app(app: Flask) -> None:
        """Initialize application configuration"""
        # Ensure all necessary directories exist
        paths = [
            Config.UPLOAD_FOLDER,
            Config.TRASH_PATH,
            Config.TEMP_UPLOAD_PATH,
            os.path.dirname(get_db_path('production'))
        ]
        
        for path in paths:
            os.makedirs(path, exist_ok=True)
        
        # Create SSL certificate directory on Windows
        if platform.system().lower() == 'windows':
            ssl_dir = os.path.dirname(Config.SSL_CERT)
            os.makedirs(ssl_dir, exist_ok=True)

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or f'sqlite:///{get_db_path("development")}'
    # Development environment specific configuration
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{get_db_path("production")}'
    # Production environment specific configuration
    PREFERRED_URL_SCHEME = 'https'

# Environment configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': ProductionConfig
} 