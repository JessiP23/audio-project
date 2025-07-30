"""
Base Audio Processor for the Audio Processing Backend.
Defines the interface for all audio effect processors.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import time
import numpy as np

logger = logging.getLogger(__name__)


class AudioEffectProcessor(ABC):
    """
    Abstract base class for audio effect processors.
    
    All audio effects must implement this interface to ensure
    consistent behavior and error handling.
    """
    
    def __init__(self, sample_rate: int = 44100):
        """
        Initialize the audio effect processor.
        
        Args:
            sample_rate: Audio sample rate in Hz
        """
        self.sample_rate = sample_rate
        self.name = self.__class__.__name__
        logger.debug(f"Initialized {self.name} with sample_rate={sample_rate}")
    
    @abstractmethod
    def apply(self, samples: List[float], parameters: Dict[str, Any]) -> List[float]:
        """
        Apply the audio effect to samples.
        
        Args:
            samples: Input audio samples
            parameters: Effect-specific parameters
            
        Returns:
            Processed audio samples
            
        Raises:
            AudioProcessingFailedError: If processing fails
        """
        pass
    
    def process_with_timing(self, samples: List[float], parameters: Dict[str, Any]) -> tuple[List[float], float]:
        """
        Apply effect with timing measurement.
        
        Args:
            samples: Input audio samples
            parameters: Effect-specific parameters
            
        Returns:
            Tuple of (processed_samples, processing_time_ms)
        """
        start_time = time.time()
        
        try:
            processed_samples = self.apply(samples, parameters)
            processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            logger.debug(f"{self.name} processed {len(samples)} samples in {processing_time:.2f}ms")
            return processed_samples, processing_time
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            logger.error(f"{self.name} failed to process {len(samples)} samples in {processing_time:.2f}ms: {e}")
            raise
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize effect parameters.
        
        Args:
            parameters: Raw parameters
            
        Returns:
            Validated and normalized parameters
        """
        # Default implementation - override in subclasses
        return parameters
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """
        Get default parameters for this effect.
        
        Returns:
            Dictionary of default parameters
        """
        # Default implementation - override in subclasses
        return {}
    
    def get_parameter_info(self) -> Dict[str, Any]:
        """
        Get information about supported parameters.
        
        Returns:
            Dictionary describing parameter types, ranges, and defaults
        """
        # Default implementation - override in subclasses
        return {
            "name": self.name,
            "description": "Audio effect processor",
            "parameters": {}
        }
    
    def _validate_samples(self, samples: List[float]) -> np.ndarray:
        """
        Validate and convert samples to numpy array.
        
        Args:
            samples: Input samples
            
        Returns:
            Numpy array of samples
            
        Raises:
            ValueError: If samples are invalid
        """
        if not samples:
            raise ValueError("Samples list cannot be empty")
        
        try:
            samples_array = np.array(samples, dtype=np.float32)
            
            # Check for invalid values
            if np.any(np.isnan(samples_array)):
                raise ValueError("Samples contain NaN values")
            
            if np.any(np.isinf(samples_array)):
                raise ValueError("Samples contain infinite values")
            
            return samples_array
            
        except Exception as e:
            raise ValueError(f"Invalid samples format: {e}")
    
    def _ensure_mono(self, samples: np.ndarray) -> np.ndarray:
        """
        Ensure samples are mono (single channel).
        
        Args:
            samples: Input samples array
            
        Returns:
            Mono samples array
        """
        if len(samples.shape) > 1:
            # Convert stereo to mono by averaging channels
            return np.mean(samples, axis=1)
        return samples
    
    def _normalize_output(self, samples: np.ndarray) -> np.ndarray:
        """
        Normalize output samples to prevent clipping.
        
        Args:
            samples: Input samples array
            
        Returns:
            Normalized samples array
        """
        max_val = np.max(np.abs(samples))
        if max_val > 1.0:
            # Normalize to prevent clipping
            samples = samples / max_val
            logger.warning(f"{self.name} output normalized to prevent clipping")
        
        return samples


class AudioProcessorFactory:
    """
    Factory for creating audio effect processors.
    
    Provides a centralized way to create and manage different
    audio effect processors.
    """
    
    _processors: Dict[str, type] = {}
    
    @classmethod
    def register(cls, effect_name: str, processor_class: type) -> None:
        """
        Register an audio effect processor.
        
        Args:
            effect_name: Name of the effect
            processor_class: Processor class to register
        """
        if not issubclass(processor_class, AudioEffectProcessor):
            raise ValueError(f"Processor class must inherit from AudioEffectProcessor")
        
        cls._processors[effect_name.lower()] = processor_class
        logger.info(f"Registered audio processor: {effect_name}")
    
    @classmethod
    def create(cls, effect_name: str, sample_rate: int = 44100) -> AudioEffectProcessor:
        """
        Create an audio effect processor.
        
        Args:
            effect_name: Name of the effect to create
            sample_rate: Audio sample rate
            
        Returns:
            AudioEffectProcessor instance
            
        Raises:
            ValueError: If effect is not supported
        """
        effect_name_lower = effect_name.lower()
        
        if effect_name_lower not in cls._processors:
            supported_effects = list(cls._processors.keys())
            raise ValueError(f"Unsupported effect '{effect_name}'. Supported effects: {supported_effects}")
        
        processor_class = cls._processors[effect_name_lower]
        return processor_class(sample_rate)
    
    @classmethod
    def get_supported_effects(cls) -> List[str]:
        """Get list of supported effect names."""
        return list(cls._processors.keys())
    
    @classmethod
    def get_effect_info(cls, effect_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific effect.
        
        Args:
            effect_name: Name of the effect
            
        Returns:
            Effect information or None if not found
        """
        try:
            processor = cls.create(effect_name)
            return processor.get_parameter_info()
        except ValueError:
            return None 