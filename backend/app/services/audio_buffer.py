"""
Audio Buffer Service for the Audio Processing Backend.
Provides thread-safe audio buffer management with circular buffer implementation.
"""

import numpy as np
from threading import Lock
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class AudioBuffer:
    """
    Thread-safe circular audio buffer for real-time audio processing.
    
    Features:
    - Circular buffer implementation with wrap-around handling
    - Thread-safe read/write operations
    - Configurable buffer size
    - Buffer status monitoring
    - Overflow/underflow protection
    """
    
    def __init__(self, size: int, sample_rate: int = 44100):
        """
        Initialize audio buffer.
        
        Args:
            size: Buffer size in samples
            sample_rate: Audio sample rate in Hz
        """
        self.size = size
        self.sample_rate = sample_rate
        self.buffer = np.zeros(size, dtype=np.float32)
        self.read_ptr = 0
        self.write_ptr = 0
        self.available = 0
        self.total_written = 0
        self.total_read = 0
        self.lock = Lock()
        self.created_at = datetime.now()
        
        logger.debug(f"Created audio buffer: size={size}, sample_rate={sample_rate}")
    
    def write(self, samples: List[float]) -> int:
        """
        Write samples to the buffer.
        
        Args:
            samples: List of audio samples to write
            
        Returns:
            Number of samples actually written
        """
        with self.lock:
            samples_to_write = min(len(samples), self.size - self.available)
            if samples_to_write == 0:
                logger.warning("Buffer full, cannot write samples")
                return 0
            
            # Convert samples to numpy array
            samples_array = np.array(samples[:samples_to_write], dtype=np.float32)
            
            # Handle wrap-around for write operation
            if self.write_ptr + samples_to_write <= self.size:
                # No wrap-around needed
                self.buffer[self.write_ptr:self.write_ptr + samples_to_write] = samples_array
            else:
                # Wrap-around needed
                first_chunk = self.size - self.write_ptr
                self.buffer[self.write_ptr:] = samples_array[:first_chunk]
                self.buffer[:samples_to_write - first_chunk] = samples_array[first_chunk:]
            
            self.write_ptr = (self.write_ptr + samples_to_write) % self.size
            self.available = min(self.available + samples_to_write, self.size)
            self.total_written += samples_to_write
            
            logger.debug(f"Wrote {samples_to_write} samples to buffer")
            return samples_to_write
    
    def read(self, num_samples: int, amplitude: float = 1.0) -> List[float]:
        """
        Read samples from buffer with optional amplitude scaling.
        
        Args:
            num_samples: Number of samples to read
            amplitude: Amplitude scaling factor
            
        Returns:
            List of audio samples
        """
        with self.lock:
            samples_to_read = min(num_samples, self.available)
            if samples_to_read == 0:
                logger.debug("No samples available for reading")
                return []
            
            result = np.zeros(samples_to_read, dtype=np.float32)
            
            # Handle wrap-around for read operation
            if self.read_ptr + samples_to_read <= self.size:
                # No wrap-around needed
                result = self.buffer[self.read_ptr:self.read_ptr + samples_to_read].copy()
            else:
                # Wrap-around needed
                first_chunk = self.size - self.read_ptr
                result[:first_chunk] = self.buffer[self.read_ptr:]
                result[first_chunk:] = self.buffer[:samples_to_read - first_chunk]
            
            # Apply amplitude scaling
            result *= amplitude
            
            self.read_ptr = (self.read_ptr + samples_to_read) % self.size
            self.available -= samples_to_read
            self.total_read += samples_to_read
            
            logger.debug(f"Read {samples_to_read} samples from buffer")
            return result.tolist()
    
    def available_samples(self) -> int:
        """Return number of samples available for reading."""
        with self.lock:
            return self.available
    
    def clear(self) -> None:
        """Clear the buffer and reset pointers."""
        with self.lock:
            self.buffer.fill(0)
            self.read_ptr = 0
            self.write_ptr = 0
            self.available = 0
            logger.info("Buffer cleared")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current buffer status for monitoring."""
        with self.lock:
            return {
                'size': self.size,
                'available': self.available,
                'read_ptr': self.read_ptr,
                'write_ptr': self.write_ptr,
                'utilization': self.available / self.size,
                'total_written': self.total_written,
                'total_read': self.total_read,
                'sample_rate': self.sample_rate,
                'created_at': self.created_at.isoformat(),
                'duration_seconds': self.available / self.sample_rate if self.sample_rate > 0 else 0
            }
    
    def is_full(self) -> bool:
        """Check if buffer is full."""
        return self.available >= self.size
    
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return self.available == 0
    
    def get_utilization(self) -> float:
        """Get buffer utilization ratio (0.0 to 1.0)."""
        return self.available / self.size


class AudioBufferManager:
    """
    Manager for multiple audio buffers.
    
    Provides centralized management of audio buffers for different sessions,
    including creation, deletion, and monitoring.
    """
    
    def __init__(self):
        """Initialize the audio buffer manager."""
        self.buffers: Dict[str, AudioBuffer] = {}
        self.lock = Lock()
        logger.info("Audio buffer manager initialized")
    
    def create_buffer(self, session_id: str, size: int = None, sample_rate: int = None) -> AudioBuffer:
        """
        Create a new audio buffer for a session.
        
        Args:
            session_id: Unique session identifier
            size: Buffer size in samples (defaults to config)
            sample_rate: Sample rate in Hz (defaults to config)
            
        Returns:
            Created AudioBuffer instance
        """
        with self.lock:
            if session_id in self.buffers:
                logger.warning(f"Buffer for session {session_id} already exists")
                return self.buffers[session_id]
            
            buffer_size = size or settings.default_buffer_size
            buffer_sample_rate = sample_rate or settings.default_sample_rate
            
            buffer = AudioBuffer(buffer_size, buffer_sample_rate)
            self.buffers[session_id] = buffer
            
            logger.info(f"Created buffer for session {session_id}: size={buffer_size}, sample_rate={buffer_sample_rate}")
            return buffer
    
    def get_buffer(self, session_id: str) -> Optional[AudioBuffer]:
        """Get buffer for a session."""
        with self.lock:
            return self.buffers.get(session_id)
    
    def delete_buffer(self, session_id: str) -> bool:
        """Delete buffer for a session."""
        with self.lock:
            if session_id in self.buffers:
                del self.buffers[session_id]
                logger.info(f"Deleted buffer for session {session_id}")
                return True
            return False
    
    def get_all_buffers(self) -> Dict[str, AudioBuffer]:
        """Get all buffers."""
        with self.lock:
            return self.buffers.copy()
    
    def get_buffer_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific buffer."""
        buffer = self.get_buffer(session_id)
        if buffer:
            return buffer.get_status()
        return None
    
    def get_all_buffer_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all buffers."""
        with self.lock:
            return {session_id: buffer.get_status() for session_id, buffer in self.buffers.items()}
    
    def clear_all_buffers(self) -> None:
        """Clear all buffers."""
        with self.lock:
            for buffer in self.buffers.values():
                buffer.clear()
            logger.info("Cleared all buffers")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get manager statistics."""
        with self.lock:
            total_buffers = len(self.buffers)
            total_samples = sum(buffer.available for buffer in self.buffers.values())
            total_utilization = sum(buffer.get_utilization() for buffer in self.buffers.values())
            avg_utilization = total_utilization / total_buffers if total_buffers > 0 else 0
            
            return {
                'total_buffers': total_buffers,
                'total_samples_available': total_samples,
                'average_utilization': avg_utilization,
                'active_sessions': list(self.buffers.keys())
            } 