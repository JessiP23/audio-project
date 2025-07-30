"""
Configuration settings for the Audio Processing Backend.
Handles environment variables, database settings, and application configuration.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
import logging
import logging.config
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = "Audio Processing API"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./audio_processing.db",
        env="DATABASE_URL"
    )
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Audio Processing
    default_sample_rate: int = Field(default=44100, env="DEFAULT_SAMPLE_RATE")
    default_buffer_size: int = Field(default=44100, env="DEFAULT_BUFFER_SIZE")
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    
    # Storage
    uploads_dir: str = Field(default="uploads", env="UPLOADS_DIR")
    processed_dir: str = Field(default="uploads/processed", env="PROCESSED_DIR")
    
    # Audio Effects
    reverb_backend: str = Field(default="pedalboard", env="REVERB_BACKEND")
    supported_audio_formats: List[str] = Field(
        default=[".wav", ".mp3", ".flac", ".ogg", ".m4a"],
        env="SUPPORTED_AUDIO_FORMATS"
    )
    
    # CORS
    cors_origins: List[str] = Field(
        default=["*"],
        env="CORS_ORIGINS"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(default=None, env="LOG_FILE")
    
    # Security
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def setup_logging() -> None:
    """Configure logging for the application."""
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.log_level,
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "app": {
                "level": settings.log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }
    
    # Add file handler if log_file is specified
    if settings.log_file:
        log_config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "level": settings.log_level,
            "formatter": "detailed",
            "filename": settings.log_file,
        }
        log_config["loggers"][""]["handlers"].append("file")
        log_config["loggers"]["app"]["handlers"].append("file")
    
    logging.config.dictConfig(log_config)


def ensure_directories() -> None:
    """Ensure required directories exist."""
    directories = [
        BASE_DIR / settings.uploads_dir,
        BASE_DIR / settings.processed_dir,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


# Initialize logging and directories
setup_logging()
ensure_directories() 