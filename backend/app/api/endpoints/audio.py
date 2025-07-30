"""
Audio Processing API Endpoints.
Provides REST API endpoints for audio processing operations.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import json
import logging
import os
from datetime import datetime
import soundfile as sf
import librosa
import numpy as np

from app.core.dependencies import get_db_session, get_audio_manager, get_audio_buffer_manager
from app.core.errors import SessionNotFoundError, AudioProcessingFailedError, EffectNotSupportedError
from app.models.pydantic import (
    CreateSessionRequest, ProcessAudioRequest, BatchProcessRequest,
    AudioSessionResponse, BufferStatusResponse, ProcessingResultResponse,
    AudioFileResponse, AudioAnalysisResponse, AudioFeaturesResponse,
    HealthCheckResponse, StatisticsResponse, SearchFilesRequest
)
from app.services.audio_processor import AudioProcessorFactory
from app.models.db import AudioSession, ProcessingHistory, AudioFile
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audio", tags=["audio"])


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    audio_manager = Depends(get_audio_manager),
    buffer_manager = Depends(get_audio_buffer_manager)
):
    """Get system health status."""
    try:
        buffer_stats = buffer_manager.get_statistics()
        
        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now(),
            version=settings.app_version,
            active_sessions=buffer_stats['total_buffers'],
            database_status="connected"
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version=settings.app_version,
            active_sessions=0,
            database_status="error"
        )


@router.post("/session", response_model=AudioSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db_session),
    buffer_manager = Depends(get_audio_buffer_manager)
):
    """Create a new audio processing session."""
    try:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create audio buffer
        buffer = buffer_manager.create_buffer(
            session_id=session_id,
            size=request.buffer_size,
            sample_rate=request.sample_rate
        )
        
        # Store in database
        db_session = AudioSession(
            session_id=session_id,
            name=request.name,
            sample_rate=request.sample_rate,
            buffer_size=request.buffer_size
        )
        db.add(db_session)
        await db.commit()
        
        logger.info(f"Created session: {session_id}")
        
        return AudioSessionResponse(
            session_id=session_id,
            name=request.name,
            created_at=db_session.created_at,
            is_active=True,
            sample_rate=request.sample_rate,
            buffer_size=request.buffer_size,
            total_samples_processed=0
        )
        
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buffers", response_model=Dict[str, BufferStatusResponse])
async def get_buffers(buffer_manager = Depends(get_audio_buffer_manager)):
    """Get all active audio buffers status."""
    try:
        buffer_statuses = buffer_manager.get_all_buffer_statuses()
        return {
            session_id: BufferStatusResponse(
                session_id=session_id,
                **status
            )
            for session_id, status in buffer_statuses.items()
        }
    except Exception as e:
        logger.error(f"Error getting buffer statuses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/write")
async def write_audio(
    session_id: str,
    samples: List[float],
    buffer_manager = Depends(get_audio_buffer_manager)
):
    """Write audio samples to a specific buffer."""
    try:
        buffer = buffer_manager.get_buffer(session_id)
        if not buffer:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        written = buffer.write(samples)
        
        return {
            "written": written,
            "available": buffer.available_samples(),
            "session_id": session_id
        }
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error writing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/read")
async def read_audio(
    session_id: str,
    num_samples: int,
    amplitude: float = 1.0,
    buffer_manager = Depends(get_audio_buffer_manager)
):
    """Read audio samples from a specific buffer."""
    try:
        buffer = buffer_manager.get_buffer(session_id)
        if not buffer:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        samples = buffer.read(num_samples, amplitude)
        
        return {
            "samples": samples,
            "available": buffer.available_samples(),
            "session_id": session_id
        }
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error reading audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{session_id}/process", response_model=ProcessingResultResponse)
async def process_audio(
    session_id: str,
    request: ProcessAudioRequest,
    db: AsyncSession = Depends(get_db_session),
    buffer_manager = Depends(get_audio_buffer_manager)
):
    """Apply audio effects to the buffer."""
    try:
        buffer = buffer_manager.get_buffer(session_id)
        if not buffer:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # Get current samples
        available = buffer.available_samples()
        if available == 0:
            raise HTTPException(status_code=400, detail="No samples available for processing")
        
        samples = buffer.read(available)
        
        # Create processor and apply effect
        processor = AudioProcessorFactory.create(request.effect.value, buffer.sample_rate)
        processed_samples, processing_time = processor.process_with_timing(samples, request.parameters)
        
        # Write processed samples back
        buffer.write(processed_samples)
        
        # Save processed audio to file
        processed_file_path = None
        try:
            processed_file_path = f"{settings.processed_dir}/processed_{session_id}_{request.effect.value}.wav"
            sf.write(processed_file_path, processed_samples, buffer.sample_rate)
        except Exception as e:
            logger.warning(f"Could not save processed file: {e}")
        
        # Log processing history
        history = ProcessingHistory(
            session_id=session_id,
            effect=request.effect.value,
            parameters=json.dumps(request.parameters),
            samples_processed=len(processed_samples),
            processing_time_ms=processing_time,
            success=True
        )
        db.add(history)
        await db.commit()
        
        logger.info(f"Processed audio for session {session_id}: {request.effect.value}")
        
        return ProcessingResultResponse(
            session_id=session_id,
            effect=request.effect.value,
            samples_processed=len(processed_samples),
            processing_time_ms=processing_time,
            success=True,
            processed_file_path=processed_file_path
        )
        
    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AudioProcessingFailedError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=AudioFileResponse)
async def upload_audio_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    audio_manager = Depends(get_audio_manager),
    buffer_manager = Depends(get_audio_buffer_manager)
):
    """Upload and process an audio file."""
    try:
        # Validate file format
        if not file.filename.lower().endswith(tuple(settings.supported_audio_formats)):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format. Supported: {settings.supported_audio_formats}"
            )
        
        # Save uploaded file
        file_path = f"{settings.uploads_dir}/{file.filename}"
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Load and analyze audio
        samples, sr = librosa.load(file_path, sr=settings.default_sample_rate)
        duration = len(samples) / sr
        
        # Convert to mono if stereo
        if len(samples.shape) > 1:
            samples = np.mean(samples, axis=1)
        
        # Create metadata
        metadata = {
            'duration': duration,
            'sample_rate': sr,
            'channels': 1,
            'format': file.filename.split('.')[-1],
            'tags': ['uploaded'],
            'samples': len(samples)
        }
        
        # Add to audio manager
        audio_file_node = await audio_manager.add_audio_file(file_path, metadata)
        
        # Create a session for this file (or get existing one)
        session_id = audio_file_node.file_id
        
        # Check if session already exists
        existing_session = await db.get(AudioSession, session_id)
        if not existing_session:
            db_session = AudioSession(
                session_id=session_id,
                name=f"Session for {file.filename}",
                sample_rate=sr,
                buffer_size=len(samples)
            )
            db.add(db_session)
            await db.commit()
        
        # Create buffer and write samples
        buffer = buffer_manager.create_buffer(
            session_id=session_id,
            size=len(samples),
            sample_rate=sr
        )
        buffer.write(samples.tolist())
        
        # Store in database
        db_file = AudioFile(
            session_id=audio_file_node.file_id,
            file_id=audio_file_node.file_id,
            filename=file.filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=audio_file_node.file_size,
            duration=duration,
            sample_rate=sr,
            channels=1,
            format=audio_file_node.format
        )
        db.add(db_file)
        await db.commit()
        
        logger.info(f"Uploaded audio file: {file.filename}")
        
        return AudioFileResponse(
            file_id=audio_file_node.file_id,
            filename=file.filename,
            original_filename=file.filename,
            file_size=audio_file_node.file_size,
            duration=duration,
            sample_rate=sr,
            channels=1,
            format=audio_file_node.format,
            uploaded_at=db_file.uploaded_at,
            tags=audio_file_node.tags,
            metadata=audio_file_node.metadata
        )
        
    except Exception as e:
        logger.error(f"Error uploading audio file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files", response_model=List[AudioFileResponse])
async def list_audio_files(
    query: str = "",
    tags: str = "",
    limit: int = 100,
    audio_manager = Depends(get_audio_manager)
):
    """List all audio files with optional filtering."""
    try:
        tag_list = tags.split(',') if tags else None
        files = await audio_manager.search_files(query, tag_list, limit)
        
        return [
            AudioFileResponse(
                file_id=file.file_id,
                filename=file.filename,
                original_filename=file.filename,
                file_size=file.file_size,
                duration=file.duration,
                sample_rate=file.sample_rate,
                channels=file.channels,
                format=file.format,
                uploaded_at=datetime.fromisoformat(file.upload_time),
                tags=file.tags,
                metadata=file.metadata
            )
            for file in files
        ]
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(audio_manager = Depends(get_audio_manager)):
    """Get audio file management statistics."""
    try:
        stats = audio_manager.get_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/processed/{session_id}/{effect}")
async def get_processed_audio(
    session_id: str,
    effect: str,
    audio_manager = Depends(get_audio_manager)
):
    """Get processed audio file."""
    try:
        # Construct the expected file path
        file_path = f"{settings.processed_dir}/processed_{session_id}_{effect}.wav"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Processed audio file not found")
        
        # Return the file
        return FileResponse(
            path=file_path,
            media_type="audio/wav",
            filename=f"processed_{session_id}_{effect}.wav"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving processed audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    buffer_manager = Depends(get_audio_buffer_manager),
    audio_manager = Depends(get_audio_manager)
):
    """Delete an audio session and clean up resources."""
    try:
        # Delete from buffer manager
        buffer_deleted = buffer_manager.delete_buffer(session_id)
        
        # Delete from audio manager
        audio_deleted = await audio_manager.delete_audio_file(session_id)
        
        if buffer_deleted or audio_deleted:
            logger.info(f"Deleted session: {session_id}")
            return {"message": f"Session {session_id} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
            
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 