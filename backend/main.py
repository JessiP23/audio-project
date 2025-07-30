from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from typing import List, Dict, Any
import logging
from datetime import datetime
import os

from audio_buffer import AudioBuffer
from audio_processor import AudioProcessor
from database import get_db, init_db
from models import AudioSession, ProcessingHistory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Audio Processing API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
os.makedirs("uploads", exist_ok=True)

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
    return {"message": "Audio Processing API is running", "status": "healthy"}

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
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Create new audio buffer and processor
    audio_buffers[session_id] = AudioBuffer(size=44100)  # 1 second at 44.1kHz
    audio_processors[session_id] = AudioProcessor()
    
    # Store in database
    async with get_db() as db:
        session = AudioSession(
            session_id=session_id,
            name=session_name,
            created_at=datetime.now()
        )
        db.add(session)
        await db.commit()
    
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
async def process_audio(session_id: str, effect: str, parameters: Dict[str, Any]):
    """Apply audio effects to the buffer."""
    if session_id not in audio_processors:
        raise HTTPException(status_code=404, detail="Session not found")
    
    processor = audio_processors[session_id]
    buffer = audio_buffers[session_id]
    
    # Get current samples and apply effect
    available = buffer.available_samples()
    if available == 0:
        raise HTTPException(status_code=400, detail="No samples available for processing")
    
    samples = buffer.read(available)
    processed_samples = processor.apply_effect(samples, effect, parameters)
    
    # Write processed samples back
    buffer.write(processed_samples)
    
    # Log processing history
    async with get_db() as db:
        history = ProcessingHistory(
            session_id=session_id,
            effect=effect,
            parameters=json.dumps(parameters),
            processed_at=datetime.now()
        )
        db.add(history)
        await db.commit()
    
    return {"processed": len(processed_samples), "effect": effect}

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
    if not file.filename.endswith(('.wav', '.mp3', '.flac', '.ogg')):
        raise HTTPException(status_code=400, detail="Unsupported audio format")
    
    # Save uploaded file
    file_path = f"uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Process the audio file
    processor = AudioProcessor()
    samples = processor.load_audio_file(file_path)
    
    # Create a new session for this file
    session_id = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    audio_buffers[session_id] = AudioBuffer(size=len(samples))
    audio_buffers[session_id].write(samples)
    
    return {
        "session_id": session_id,
        "filename": file.filename,
        "samples": len(samples),
        "duration": len(samples) / 44100  # Assuming 44.1kHz sample rate
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 