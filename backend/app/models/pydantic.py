"""
Pydantic schemas for the Audio Processing Backend.
Defines request and response models for API validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EffectType(str, Enum):
    """Supported audio effect types."""
    REVERB = "reverb"
    DELAY = "delay"
    DISTORTION = "distortion"
    FILTER = "filter"
    COMPRESSION = "compression"
    CHORUS = "chorus"
    FLANGER = "flanger"
    PHASER = "phaser"
    EQUALIZER = "equalizer"
    NORMALIZE = "normalize"


# Request Models
class CreateSessionRequest(BaseModel):
    """Request model for creating a new audio session."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Session name")
    session_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Session name (alternative field)")
    sample_rate: Optional[int] = Field(default=44100, ge=8000, le=192000, description="Sample rate in Hz")
    buffer_size: Optional[int] = Field(default=44100, ge=1024, le=441000, description="Buffer size in samples")
    
    def __init__(self, **data):
        super().__init__(**data)
        # Handle both 'name' and 'session_name' fields
        if self.session_name and not self.name:
            self.name = self.session_name
        elif not self.name:
            self.name = "Default Session"


class ProcessAudioRequest(BaseModel):
    """Request model for processing audio with effects."""
    effect: EffectType = Field(..., description="Audio effect to apply")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Effect parameters")


class BatchProcessRequest(BaseModel):
    """Request model for batch processing multiple effects."""
    effects: List[ProcessAudioRequest] = Field(..., min_items=1, max_items=10, description="List of effects to apply")


class UploadAudioRequest(BaseModel):
    """Request model for audio file upload metadata."""
    tags: Optional[List[str]] = Field(default_factory=list, description="Audio file tags")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class SearchFilesRequest(BaseModel):
    """Request model for searching audio files."""
    query: Optional[str] = Field(default="", description="Search query")
    tags: Optional[List[str]] = Field(default_factory=list, description="Filter by tags")
    limit: Optional[int] = Field(default=100, ge=1, le=1000, description="Maximum number of results")


# Response Models
class AudioSessionResponse(BaseModel):
    """Response model for audio session information."""
    session_id: str = Field(..., description="Unique session identifier")
    name: str = Field(..., description="Session name")
    created_at: datetime = Field(..., description="Session creation timestamp")
    is_active: bool = Field(..., description="Session active status")
    sample_rate: int = Field(..., description="Session sample rate")
    buffer_size: int = Field(..., description="Session buffer size")
    total_samples_processed: int = Field(..., description="Total samples processed")
    
    class Config:
        from_attributes = True


class BufferStatusResponse(BaseModel):
    """Response model for audio buffer status."""
    session_id: str = Field(..., description="Session identifier")
    size: int = Field(..., description="Buffer size in samples")
    available: int = Field(..., description="Available samples for reading")
    utilization: float = Field(..., ge=0.0, le=1.0, description="Buffer utilization ratio")
    read_ptr: int = Field(..., description="Read pointer position")
    write_ptr: int = Field(..., description="Write pointer position")


class ProcessingResultResponse(BaseModel):
    """Response model for audio processing results."""
    session_id: str = Field(..., description="Session identifier")
    effect: str = Field(..., description="Applied effect")
    samples_processed: int = Field(..., description="Number of samples processed")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    success: bool = Field(..., description="Processing success status")
    processed_file_path: Optional[str] = Field(None, description="Path to processed audio file")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")


class AudioFileResponse(BaseModel):
    """Response model for audio file information."""
    file_id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="File name")
    original_filename: str = Field(..., description="Original uploaded filename")
    file_size: int = Field(..., description="File size in bytes")
    duration: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(..., description="Audio sample rate")
    channels: int = Field(..., description="Number of audio channels")
    format: str = Field(..., description="Audio format")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    tags: List[str] = Field(default_factory=list, description="File tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="File metadata")
    
    class Config:
        from_attributes = True


class AudioAnalysisResponse(BaseModel):
    """Response model for audio analysis results."""
    session_id: str = Field(..., description="Session identifier")
    rms_level: float = Field(..., description="RMS level")
    peak_level: float = Field(..., description="Peak level")
    dynamic_range: float = Field(..., description="Dynamic range")
    spectral_centroid: float = Field(..., description="Spectral centroid")
    spectral_rolloff: float = Field(..., description="Spectral rolloff")
    zero_crossing_rate: float = Field(..., description="Zero crossing rate")
    duration: float = Field(..., description="Audio duration")
    sample_rate: int = Field(..., description="Sample rate")


class AudioFeaturesResponse(BaseModel):
    """Response model for extracted audio features."""
    session_id: str = Field(..., description="Session identifier")
    mfcc_mean: List[float] = Field(..., description="MFCC mean values")
    mfcc_std: List[float] = Field(..., description="MFCC standard deviation values")
    chroma_mean: List[float] = Field(..., description="Chroma mean values")
    spectral_centroids_mean: float = Field(..., description="Mean spectral centroids")
    spectral_rolloff_mean: float = Field(..., description="Mean spectral rolloff")
    tempo: float = Field(..., description="Detected tempo")
    harmonic_ratio: float = Field(..., description="Harmonic to percussive ratio")
    duration: float = Field(..., description="Audio duration")


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    active_sessions: int = Field(..., description="Number of active sessions")
    database_status: str = Field(..., description="Database connection status")


class StatisticsResponse(BaseModel):
    """Response model for system statistics."""
    total_files: int = Field(..., description="Total number of audio files")
    total_size: int = Field(..., description="Total size of all files in bytes")
    cache_size: int = Field(..., description="Number of cached files")
    tree_height: int = Field(..., description="AVL tree height")
    average_file_size: float = Field(..., description="Average file size in bytes")
    storage_path: str = Field(..., description="Storage directory path")


class ErrorResponse(BaseModel):
    """Response model for error messages."""
    error: Dict[str, Any] = Field(..., description="Error information")


# WebSocket Models
class WebSocketMessage(BaseModel):
    """Base model for WebSocket messages."""
    type: str = Field(..., description="Message type")


class AudioDataMessage(WebSocketMessage):
    """WebSocket message for audio data."""
    type: str = Field(default="audio_data", description="Message type")
    samples: List[float] = Field(..., description="Audio samples")


class EffectRequestMessage(WebSocketMessage):
    """WebSocket message for effect requests."""
    type: str = Field(default="effect_request", description="Message type")
    effect: str = Field(..., description="Effect to apply")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Effect parameters")


class BufferStatusMessage(WebSocketMessage):
    """WebSocket message for buffer status updates."""
    type: str = Field(default="buffer_status", description="Message type")
    status: BufferStatusResponse = Field(..., description="Buffer status")
    written: int = Field(..., description="Number of samples written")


class ProcessedAudioMessage(WebSocketMessage):
    """WebSocket message for processed audio data."""
    type: str = Field(default="processed_audio", description="Message type")
    samples: List[float] = Field(..., description="Processed audio samples")


class EffectAppliedMessage(WebSocketMessage):
    """WebSocket message for effect application confirmation."""
    type: str = Field(default="effect_applied", description="Message type")
    effect: str = Field(..., description="Applied effect")
    processed_samples: int = Field(..., description="Number of processed samples") 