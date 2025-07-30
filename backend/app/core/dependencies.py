"""
FastAPI dependencies for the Audio Processing Backend.
Provides database sessions, authentication, and other common dependencies.
"""

from typing import AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_async_session
from app.services.audio_manager import AudioFileManager
from app.services.audio_buffer import AudioBufferManager
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global singleton instances
_audio_manager = None
_buffer_manager = None


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async for session in get_async_session():
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

async def get_audio_manager() -> AudioFileManager:
    """Dependency to get audio file manager."""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioFileManager()
    return _audio_manager

async def get_audio_buffer_manager() -> AudioBufferManager:
    """Dependency to get audio buffer manager."""
    global _buffer_manager
    if _buffer_manager is None:
        _buffer_manager = AudioBufferManager()
    return _buffer_manager


def get_current_user_id() -> Optional[str]:
    """Get current user ID from request context (placeholder for future authentication)."""
    return "default_user"


def validate_session_id(session_id: str) -> str:
    """Validate session ID format."""
    if not session_id or len(session_id) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format"
        )
    return session_id


def validate_file_size(file_size: int) -> int:
    """Validate uploaded file size."""
    max_size = settings.max_file_size_mb * 1024 * 1024  # Convert to bytes
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
        )
    return file_size


def validate_audio_format(filename: str) -> str:
    """Validate audio file format."""
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required"
        )
    
    file_extension = filename.lower().split('.')[-1]
    supported_formats = [fmt.replace('.', '') for fmt in settings.supported_audio_formats]
    
    if file_extension not in supported_formats:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format. Supported formats: {', '.join(supported_formats)}"
        )
    
    return filename 