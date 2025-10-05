import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent


class Config:
    """Base configuration."""

    # Secret key for session management and CSRF protection
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f'sqlite:///{BASE_DIR / "blog.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # WTForms configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get("CSRF_SECRET_KEY") or SECRET_KEY

    # GitHub OAuth configuration
    GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET")
    GITHUB_CALLBACK_URL = (
        os.environ.get("GITHUB_CALLBACK_URL") or "http://localhost:5000/auth/github/callback"
    )

    # Admin configuration
    ADMIN_GITHUB_USERNAME = os.environ.get("ADMIN_GITHUB_USERNAME")

    # Upload configuration
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

    # Image processing configuration
    IMAGE_MAX_WIDTH = 1920  # Maximum width for uploaded images
    IMAGE_MAX_HEIGHT = 1920  # Maximum height for uploaded images
    IMAGE_QUALITY = 85  # JPEG quality (1-100)
    IMAGE_THUMBNAIL_SIZE = (400, 400)  # Thumbnail size
    IMAGE_SOCIAL_SIZE = (1200, 630)  # Social media share size


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
