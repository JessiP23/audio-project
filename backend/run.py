#!/usr/bin/env python3
"""
Simple script to run the new audio processing backend.
"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    print("🎵 Starting Audio Processing Backend...")
    print(f"Version: {settings.app_version}")
    print(f"Host: {settings.host}")
    print(f"Port: {settings.port}")
    print(f"Debug: {settings.debug}")
    print(f"Sample Rate: {settings.default_sample_rate}Hz")
    print(f"Buffer Size: {settings.default_buffer_size} samples")
    print("\nStarting server...")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 