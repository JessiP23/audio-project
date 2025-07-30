"""
Main FastAPI Application for the Audio Processing Backend.
Entry point for the audio processing API with all routes and middleware.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import json
import logging
from datetime import datetime

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.db.session import init_db, close_db, check_db_connection
from app.api.endpoints import audio
from app.services.audio_processor import AudioProcessorFactory

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="High-performance audio processing API with real-time effects",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Mount static files
app.mount("/uploads", StaticFiles(directory=settings.uploads_dir), name="uploads")

# Include routers
app.include_router(audio.router)

# WebSocket connections
active_connections: list[WebSocket] = []


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        # Initialize database
        await init_db()
        
        # Check database connection
        db_connected = await check_db_connection()
        if not db_connected:
            logger.error("Database connection failed")
        
        # Log startup information
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Supported effects: {AudioProcessorFactory.get_supported_effects()}")
        logger.info(f"Storage path: {settings.uploads_dir}")
        logger.info(f"Sample rate: {settings.default_sample_rate}Hz")
        logger.info(f"Buffer size: {settings.default_buffer_size} samples")
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    try:
        # Close database connections
        await close_db()
        
        # Close WebSocket connections
        for connection in active_connections:
            await connection.close()
        
        logger.info("Application shutdown completed")
        
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "health": "/api/audio/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        db_connected = await check_db_connection()
        
        return {
            "status": "healthy" if db_connected else "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": settings.app_version,
            "database": "connected" if db_connected else "disconnected",
            "effects": AudioProcessorFactory.get_supported_effects()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "version": settings.app_version,
            "error": str(e)
        }


@app.websocket("/ws/audio/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time audio streaming."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        logger.info(f"WebSocket connected for session: {session_id}")
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "audio_data":
                # Handle audio data
                samples = message["samples"]
                # TODO: Process audio data in real-time
                await websocket.send_text(json.dumps({
                    "type": "audio_received",
                    "samples_count": len(samples),
                    "session_id": session_id
                }))
                
            elif message["type"] == "effect_request":
                # Handle effect request
                effect = message["effect"]
                parameters = message.get("parameters", {})
                
                # TODO: Apply effect in real-time
                await websocket.send_text(json.dumps({
                    "type": "effect_applied",
                    "effect": effect,
                    "session_id": session_id
                }))
                
            elif message["type"] == "ping":
                # Handle ping
                await websocket.send_text(json.dumps({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }))
    
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        active_connections.remove(websocket)


@app.get("/api/effects")
async def get_supported_effects():
    """Get list of supported audio effects."""
    try:
        effects = AudioProcessorFactory.get_supported_effects()
        effect_info = {}
        
        for effect in effects:
            info = AudioProcessorFactory.get_effect_info(effect)
            if info:
                effect_info[effect] = info
        
        return {
            "supported_effects": effects,
            "effect_info": effect_info,
            "total_effects": len(effects)
        }
    except Exception as e:
        logger.error(f"Error getting effects: {e}")
        raise


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 