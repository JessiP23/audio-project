"""
Custom error handlers and exception classes for the Audio Processing Backend.
Provides consistent error responses and proper HTTP status codes.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from typing import Any, Dict, Union

logger = logging.getLogger(__name__)


class AudioProcessingError(Exception):
    """Base exception for audio processing errors."""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AudioFileNotFoundError(AudioProcessingError):
    """Raised when an audio file is not found."""
    pass


class AudioFormatNotSupportedError(AudioProcessingError):
    """Raised when the audio format is not supported."""
    pass


class AudioProcessingFailedError(AudioProcessingError):
    """Raised when audio processing fails."""
    pass


class SessionNotFoundError(AudioProcessingError):
    """Raised when an audio session is not found."""
    pass


class BufferOverflowError(AudioProcessingError):
    """Raised when the audio buffer overflows."""
    pass


class EffectNotSupportedError(AudioProcessingError):
    """Raised when an audio effect is not supported."""
    pass


def create_error_response(
    message: str,
    error_code: str = None,
    status_code: int = 500,
    details: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "error": {
            "message": message,
            "code": error_code or "INTERNAL_ERROR",
            "status_code": status_code,
            "details": details or {}
        }
    }


async def audio_processing_exception_handler(request: Request, exc: AudioProcessingError) -> JSONResponse:
    """Handle AudioProcessingError exceptions."""
    logger.error(f"Audio processing error: {exc.message}", extra={
        "error_code": exc.error_code,
        "details": exc.details,
        "path": request.url.path
    })
    
    status_code = 500
    if isinstance(exc, AudioFileNotFoundError):
        status_code = 404
    elif isinstance(exc, AudioFormatNotSupportedError):
        status_code = 400
    elif isinstance(exc, SessionNotFoundError):
        status_code = 404
    elif isinstance(exc, BufferOverflowError):
        status_code = 400
    elif isinstance(exc, EffectNotSupportedError):
        status_code = 400
    
    return JSONResponse(
        status_code=status_code,
        content=create_error_response(
            message=exc.message,
            error_code=exc.error_code,
            status_code=status_code,
            details=exc.details
        )
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}", extra={
        "path": request.url.path,
        "body": exc.body
    })
    
    return JSONResponse(
        status_code=422,
        content=create_error_response(
            message="Validation error",
            error_code="VALIDATION_ERROR",
            status_code=422,
            details={"errors": exc.errors()}
        )
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP error {exc.status_code}: {exc.detail}", extra={
        "path": request.url.path,
        "status_code": exc.status_code
    })
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            message=str(exc.detail),
            error_code=f"HTTP_{exc.status_code}",
            status_code=exc.status_code
        )
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True, extra={
        "path": request.url.path,
        "exception_type": type(exc).__name__
    })
    
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            message="Internal server error",
            error_code="INTERNAL_ERROR",
            status_code=500
        )
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(AudioProcessingError, audio_processing_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 