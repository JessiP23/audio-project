from threading import Lock
import numpy as np
from typing import List, Optional


class AudioBuffer:
    def __init__(self, size: int):
        """Initialize the audio buffer with given size."""
        self.size = size
        self.buffer = np.zeros(size, dtype=np.float32)
        self.read_ptr = 0
        self.write_ptr = 0
        self.available = 0
        self.lock = Lock()

    def write(self, samples: List[float]) -> int:
        """Write samples to the buffer. Return number of samples written."""
        with self.lock:
            samples_to_write = min(len(samples), self.size - self.available)
            if samples_to_write == 0:
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
            
            return samples_to_write

    def read(self, num_samples: int, amplitude: float = 1.0) -> List[float]:
        """Read samples from buffer with optional amplitude scaling."""
        with self.lock:
            samples_to_read = min(num_samples, self.available)
            if samples_to_read == 0:
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
            
            return result.tolist()

    def available_samples(self) -> int:
        """Return number of samples available for reading."""
        with self.lock:
            return self.available

    def clear(self):
        """Clear the buffer and reset pointers."""
        with self.lock:
            self.buffer.fill(0)
            self.read_ptr = 0
            self.write_ptr = 0
            self.available = 0

    def get_buffer_status(self) -> dict:
        """Get current buffer status for monitoring."""
        with self.lock:
            return {
                'size': self.size,
                'available': self.available,
                'read_ptr': self.read_ptr,
                'write_ptr': self.write_ptr,
                'utilization': self.available / self.size
            }


# Example test cases:
def test_audio_buffer():
    buffer = AudioBuffer(1000)

    # Test 1: Basic Write & Read
    result = buffer.write([0.1] * 100)
    assert result == 100
    assert buffer.available_samples() == 100
    samples = buffer.read(50, amplitude=2.0)
    assert len(samples) == 50
    assert all(abs(s - 0.2) < 1e-6 for s in samples)
    assert buffer.available_samples() == 50  # 50 samples should remain

    # Test 2: Circular Wrap-Around
    buffer.write([0.5] * 990)  # This should fill the buffer
    assert buffer.available_samples() == 1000
    samples = buffer.read(100)  # Read 100 samples
    assert len(samples) == 100
    assert buffer.available_samples() == 900  # 900 should remain

    # Test 3: Overflow Prevention
    assert buffer.write([0.1] * 2000) == 100  # Should only write 100 (buffer maxed out)

    # Test 4: Underflow Handling
    buffer.read(1000)  # Read 1000 available samples
    assert buffer.available_samples() == 0
    assert len(buffer.read(50)) == 0  # Should return an empty list

    print("All tests passed!")


if __name__ == "__main__":
    test_audio_buffer() 