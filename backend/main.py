from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import asyncio
from typing import List, Dict, Any
import logging
from datetime import datetime
import os
import numpy as np
import librosa

from audio_buffer import AudioBuffer
from audio_processor import AudioProcessor
from database import get_db, init_db, AsyncSessionLocal
from models import AudioSession, ProcessingHistory
from audio_manager import audio_manager

# Pydantic models for request validation
class ProcessAudioRequest(BaseModel):
    effect: str
    parameters: Dict[str, Any] = {}

class BatchProcessRequest(BaseModel):
    effects: List[Dict[str, Any]]

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('audio_processing.log')
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Audio Processing API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Global audio buffers and processors
audio_buffers: Dict[str, AudioBuffer] = {}
audio_processors: Dict[str, AudioProcessor] = {}
active_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialize database and create default audio buffers."""
    await init_db()
    logger.info("Audio Processing API started")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources."""
    for connection in active_connections:
        await connection.close()
    logger.info("Audio Processing API shutdown")

@app.get("/")
async def root():
    """Health check endpoint."""
    logger.info("Health check requested")
    return {
        "message": "David AI Audio Processing API is running", 
        "status": "healthy",
        "version": "1.0.0",
        "active_sessions": len(audio_buffers),
        "active_processors": len(audio_processors)
    }

@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    logger.info("Detailed health check requested")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(audio_buffers),
        "active_processors": len(audio_processors),
        "database": "connected" if audio_buffers else "no_sessions"
    }

@app.get("/api/audio/buffers")
async def get_buffers():
    """Get all active audio buffers status."""
    buffer_status = {}
    for session_id, buffer in audio_buffers.items():
        buffer_status[session_id] = buffer.get_buffer_status()
    return buffer_status

@app.post("/api/audio/session")
async def create_session(session_name: str = "default"):
    """Create a new audio processing session."""
    logger.info(f"Creating new session with name: {session_name}")
    
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logger.debug(f"Generated session ID: {session_id}")
    
    # Create new audio buffer and processor
    audio_buffers[session_id] = AudioBuffer(size=44100)  # 1 second at 44.1kHz
    audio_processors[session_id] = AudioProcessor()
    logger.debug(f"Created audio buffer and processor for session {session_id}")
    
    # Store in database
    try:
        from database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            session = AudioSession(
                session_id=session_id,
                name=session_name,
                created_at=datetime.now()
            )
            db.add(session)
            await db.commit()
            logger.info(f"Session {session_id} stored in database successfully")
    except Exception as e:
        logger.error(f"Database error: {e}")
        # Continue without database if there's an error
    
    logger.info(f"Session {session_id} created successfully")
    return {"session_id": session_id, "name": session_name}

@app.post("/api/audio/{session_id}/write")
async def write_audio(session_id: str, samples: List[float]):
    """Write audio samples to a specific buffer."""
    if session_id not in audio_buffers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    buffer = audio_buffers[session_id]
    written = buffer.write(samples)
    
    return {"written": written, "available": buffer.available_samples()}

@app.post("/api/audio/{session_id}/read")
async def read_audio(session_id: str, num_samples: int, amplitude: float = 1.0):
    """Read audio samples from a specific buffer."""
    if session_id not in audio_buffers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    buffer = audio_buffers[session_id]
    samples = buffer.read(num_samples, amplitude)
    
    return {"samples": samples, "available": buffer.available_samples()}

@app.post("/api/audio/{session_id}/process")
async def process_audio(session_id: str, request: ProcessAudioRequest):
    """Apply audio effects to the buffer."""
    logger.info(f"Processing audio for session {session_id} with effect: {request.effect}")
    logger.debug(f"Effect parameters: {request.parameters}")
    
    if session_id not in audio_processors:
        logger.error(f"Session {session_id} not found in audio_processors")
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session_id not in audio_buffers:
        logger.error(f"Session {session_id} not found in audio_buffers")
        raise HTTPException(status_code=404, detail="Session not found")
    
    processor = audio_processors[session_id]
    buffer = audio_buffers[session_id]
    
    # Get current samples and apply effect
    available = buffer.available_samples()
    logger.debug(f"Available samples in buffer: {available}")
    
    if available == 0:
        logger.warning(f"No samples available for processing in session {session_id}")
        raise HTTPException(status_code=400, detail="No samples available for processing")
    
    samples = buffer.read(available)
    logger.debug(f"Read {len(samples)} samples from buffer")
    
    try:
        processed_samples = processor.apply_effect(samples, request.effect, request.parameters)
        logger.info(f"Successfully applied {request.effect} effect to {len(processed_samples)} samples")
    except Exception as e:
        logger.error(f"Error applying effect {request.effect}: {e}")
        raise HTTPException(status_code=500, detail=f"Error applying effect: {str(e)}")
    
    # Write processed samples back
    buffer.write(processed_samples)
    logger.debug(f"Wrote {len(processed_samples)} processed samples back to buffer")
    
    # Save processed audio to file for playback
    try:
        import soundfile as sf
        processed_file_path = f"uploads/processed_{session_id}_{request.effect}.wav"
        sf.write(processed_file_path, processed_samples, 44100)
        logger.info(f"Processed audio saved to: {processed_file_path}")
    except Exception as e:
        logger.error(f"Error saving processed audio: {e}")
        processed_file_path = None
    
    # Log processing history
    try:
        from database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            history = ProcessingHistory(
                session_id=session_id,
                effect=request.effect,
                parameters=json.dumps(request.parameters),
                processed_at=datetime.now()
            )
            db.add(history)
            await db.commit()
            logger.debug(f"Processing history logged to database")
    except Exception as e:
        logger.error(f"Database error in process_audio: {e}")
        # Continue without database logging if there's an error
    
    # Update AVL tree processing history
    try:
        await audio_manager.update_processing_history(
            session_id, 
            request.effect, 
            request.parameters, 
            {"processed": len(processed_samples), "effect": request.effect}
        )
        logger.debug(f"AVL tree processing history updated")
    except Exception as e:
        logger.error(f"AVL tree error in process_audio: {e}")
        # Continue without AVL tree logging if there's an error
    
    logger.info(f"Audio processing completed successfully for session {session_id}")
    return {
        "processed": len(processed_samples), 
        "effect": request.effect,
        "processed_file": processed_file_path,
        "session_id": session_id
    }

@app.websocket("/ws/audio/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time audio streaming."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Receive audio data from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "audio_data":
                samples = message["samples"]
                
                if session_id in audio_buffers:
                    buffer = audio_buffers[session_id]
                    written = buffer.write(samples)
                    
                    # Send back buffer status
                    status = buffer.get_buffer_status()
                    await websocket.send_text(json.dumps({
                        "type": "buffer_status",
                        "status": status,
                        "written": written
                    }))
                    
                    # If buffer is getting full, process and send back
                    if status["utilization"] > 0.8:
                        available = buffer.available_samples()
                        if available > 0:
                            processed_samples = buffer.read(available, amplitude=1.0)
                            await websocket.send_text(json.dumps({
                                "type": "processed_audio",
                                "samples": processed_samples
                            }))
            
            elif message["type"] == "effect_request":
                effect = message["effect"]
                parameters = message.get("parameters", {})
                
                if session_id in audio_processors:
                    processor = audio_processors[session_id]
                    buffer = audio_buffers[session_id]
                    
                    available = buffer.available_samples()
                    if available > 0:
                        samples = buffer.read(available)
                        processed_samples = processor.apply_effect(samples, effect, parameters)
                        buffer.write(processed_samples)
                        
                        await websocket.send_text(json.dumps({
                            "type": "effect_applied",
                            "effect": effect,
                            "processed_samples": len(processed_samples)
                        }))
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected for session {session_id}")

@app.post("/api/audio/upload")
async def upload_audio_file(file: UploadFile = File(...)):
    """Upload and process an audio file."""
    logger.info(f"Uploading audio file: {file.filename}")
    
    if not file.filename.endswith(('.wav', '.mp3', '.flac', '.ogg')):
        logger.error(f"Unsupported audio format: {file.filename}")
        raise HTTPException(status_code=400, detail="Unsupported audio format")
    
    # Save uploaded file
    file_path = f"uploads/{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        logger.debug(f"File saved to: {file_path}")
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        raise HTTPException(status_code=500, detail="Error saving file")
    
    # Process the audio file
    processor = AudioProcessor()
    try:
        samples = processor.load_audio_file(file_path)
        logger.info(f"Loaded {len(samples)} samples from {file.filename}")
    except Exception as e:
        logger.error(f"Error loading audio file: {e}")
        raise HTTPException(status_code=500, detail="Error loading audio file")
    
    # Add to AVL tree manager
    try:
        # Convert samples to numpy array for shape analysis
        import numpy as np
        samples_array = np.array(samples)
        
        metadata = {
            'duration': len(samples) / 44100,
            'sample_rate': 44100,
            'channels': 1 if len(samples_array.shape) == 1 else samples_array.shape[1],
            'format': file.filename.split('.')[-1],
            'tags': ['uploaded', 'processed'],
            'samples': len(samples)
        }
        
        audio_file_node = await audio_manager.add_audio_file(file_path, metadata)
        session_id = audio_file_node.file_id
        
        logger.info(f"Added file to AVL tree: {session_id}")
        
    except Exception as e:
        logger.error(f"Error adding to AVL tree: {e}")
        # Fallback to original session ID generation if AVL tree fails
        session_id = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.warning(f"AVL tree failed, using fallback session ID: {session_id}")
    
    # Create audio buffer and processor
    audio_buffers[session_id] = AudioBuffer(size=len(samples))
    audio_processors[session_id] = AudioProcessor()
    
    try:
        audio_buffers[session_id].write(samples)
        logger.info(f"Created session {session_id} with {len(samples)} samples")
    except Exception as e:
        logger.error(f"Error writing samples to buffer: {e}")
        raise HTTPException(status_code=500, detail="Error processing audio")
    
    duration = len(samples) / 44100  # Assuming 44.1kHz sample rate
    logger.info(f"Audio file processed successfully. Duration: {duration:.2f}s")
    
    return {
        "session_id": session_id,
        "filename": file.filename,
        "samples": len(samples),
        "duration": duration,
        "file_id": session_id
    }

@app.post("/api/audio/{session_id}/analyze")
async def analyze_audio_session(session_id: str):
    """Analyze audio characteristics for research purposes."""
    if session_id not in audio_buffers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    buffer = audio_buffers[session_id]
    available = buffer.available_samples()
    
    if available == 0:
        raise HTTPException(status_code=400, detail="No samples available for analysis")
    
    samples = buffer.read(available)
    processor = audio_processors[session_id]
    
    # Basic analysis
    analysis = processor.analyze_audio(samples)
    
    # Advanced feature extraction for AI/ML
    features = processor.extract_features(samples)
    
    # Write samples back to buffer
    buffer.write(samples)
    
    return {
        "session_id": session_id,
        "analysis": analysis,
        "features": features,
        "samples_analyzed": available
    }

@app.post("/api/audio/{session_id}/extract-features")
async def extract_audio_features(session_id: str, feature_type: str = "all"):
    """Extract specific audio features for machine learning datasets."""
    if session_id not in audio_buffers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    buffer = audio_buffers[session_id]
    available = buffer.available_samples()
    
    if available == 0:
        raise HTTPException(status_code=400, detail="No samples available for feature extraction")
    
    samples = buffer.read(available)
    processor = audio_processors[session_id]
    
    features = {}
    
    if feature_type in ["all", "mfcc"]:
        # MFCC features for speech recognition
        mfccs = librosa.feature.mfcc(y=np.array(samples), sr=processor.sample_rate, n_mfcc=13)
        features["mfcc"] = {
            "mean": np.mean(mfccs, axis=1).tolist(),
            "std": np.std(mfccs, axis=1).tolist(),
            "delta": librosa.feature.delta(mfccs).tolist()
        }
    
    if feature_type in ["all", "spectral"]:
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=np.array(samples), sr=processor.sample_rate)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=np.array(samples), sr=processor.sample_rate)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=np.array(samples), sr=processor.sample_rate)
        
        features["spectral"] = {
            "centroids": spectral_centroids.tolist(),
            "rolloff": spectral_rolloff.tolist(),
            "bandwidth": spectral_bandwidth.tolist()
        }
    
    if feature_type in ["all", "rhythm"]:
        # Rhythm and tempo features
        tempo, beats = librosa.beat.beat_track(y=np.array(samples), sr=processor.sample_rate)
        features["rhythm"] = {
            "tempo": float(tempo),
            "beat_frames": beats.tolist(),
            "beat_times": librosa.frames_to_time(beats, sr=processor.sample_rate).tolist()
        }
    
    if feature_type in ["all", "chroma"]:
        # Chroma features for musical analysis
        chroma = librosa.feature.chroma_stft(y=np.array(samples), sr=processor.sample_rate)
        features["chroma"] = {
            "chroma_stft": chroma.tolist(),
            "chroma_cqt": librosa.feature.chroma_cqt(y=np.array(samples), sr=processor.sample_rate).tolist()
        }
    
    # Write samples back to buffer
    buffer.write(samples)
    
    return {
        "session_id": session_id,
        "feature_type": feature_type,
        "features": features,
        "samples_processed": available
    }

@app.post("/api/audio/{session_id}/batch-process")
async def batch_process_effects(session_id: str, request: BatchProcessRequest):
    """Apply multiple effects in sequence for batch processing."""
    if session_id not in audio_processors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    processor = audio_processors[session_id]
    buffer = audio_buffers[session_id]
    
    available = buffer.available_samples()
    if available == 0:
        raise HTTPException(status_code=400, detail="No samples available for processing")
    
    samples = buffer.read(available)
    processed_samples = samples
    applied_effects = []
    
    for effect_config in request.effects:
        effect_name = effect_config.get("effect")
        parameters = effect_config.get("parameters", {})
        
        if effect_name:
            processed_samples = processor.apply_effect(processed_samples, effect_name, parameters)
            applied_effects.append(effect_name)
    
    # Write processed samples back
    buffer.write(processed_samples)
    
    # Log processing history
    try:
        from database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            for effect in applied_effects:
                history = ProcessingHistory(
                    session_id=session_id,
                    effect=effect,
                    parameters=json.dumps({"batch_processed": True}),
                    processed_at=datetime.now()
                )
                db.add(history)
            await db.commit()
    except Exception as e:
        logger.error(f"Database error in batch_process: {e}")
    
    return {
        "session_id": session_id,
        "applied_effects": applied_effects,
        "samples_processed": len(processed_samples)
    }

@app.get("/api/audio/sessions")
async def list_sessions():
    """List all active audio sessions."""
    sessions = []
    for session_id, buffer in audio_buffers.items():
        status = buffer.get_buffer_status()
        sessions.append({
            "session_id": session_id,
            "buffer_status": status,
            "has_processor": session_id in audio_processors
        })
    return {"sessions": sessions}

@app.delete("/api/audio/{session_id}")
async def delete_session(session_id: str):
    """Delete an audio session and clean up resources."""
    # Delete from AVL tree
    success = await audio_manager.delete_audio_file(session_id)
    
    # Delete from memory
    if session_id in audio_buffers:
        del audio_buffers[session_id]
    if session_id in audio_processors:
        del audio_processors[session_id]
    
    if success:
        return {"message": f"Session {session_id} deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.get("/api/audio/files")
async def list_audio_files(query: str = "", tags: str = "", limit: int = 100):
    """List all audio files with optional filtering."""
    try:
        tag_list = tags.split(',') if tags else None
        files = await audio_manager.search_files(query, tag_list, limit)
        
        return {
            "files": [
                {
                    "file_id": file.file_id,
                    "filename": file.filename,
                    "duration": file.duration,
                    "file_size": file.file_size,
                    "upload_time": file.upload_time,
                    "access_count": file.access_count,
                    "tags": file.tags
                }
                for file in files
            ],
            "total": len(files),
            "query": query,
            "tags": tag_list
        }
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail="Error listing files")

@app.get("/api/audio/files/popular")
async def get_popular_files(limit: int = 10):
    """Get most accessed audio files."""
    try:
        files = await audio_manager.get_popular_files(limit)
        return {
            "files": [
                {
                    "file_id": file.file_id,
                    "filename": file.filename,
                    "access_count": file.access_count,
                    "duration": file.duration
                }
                for file in files
            ]
        }
    except Exception as e:
        logger.error(f"Error getting popular files: {e}")
        raise HTTPException(status_code=500, detail="Error getting popular files")

@app.get("/api/audio/files/recent")
async def get_recent_files(limit: int = 10):
    """Get recently uploaded audio files."""
    try:
        files = await audio_manager.get_recent_files(limit)
        return {
            "files": [
                {
                    "file_id": file.file_id,
                    "filename": file.filename,
                    "upload_time": file.upload_time,
                    "duration": file.duration
                }
                for file in files
            ]
        }
    except Exception as e:
        logger.error(f"Error getting recent files: {e}")
        raise HTTPException(status_code=500, detail="Error getting recent files")

@app.get("/api/audio/statistics")
async def get_audio_statistics():
    """Get audio file management statistics."""
    try:
        stats = audio_manager.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail="Error getting statistics")

@app.get("/api/audio/processed/{session_id}/{effect}")
async def get_processed_audio(session_id: str, effect: str):
    """Get processed audio file for a specific session and effect."""
    try:
        file_path = f"uploads/processed_{session_id}_{effect}.wav"
        if os.path.exists(file_path):
            return FileResponse(file_path, media_type="audio/wav")
        else:
            raise HTTPException(status_code=404, detail="Processed audio file not found")
    except Exception as e:
        logger.error(f"Error serving processed audio: {e}")
        raise HTTPException(status_code=500, detail="Error serving processed audio")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 