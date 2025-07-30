"""
Reverb Audio Processor using Pedalboard library.
Provides high-quality reverb effects using Spotify's Pedalboard library.
"""

from typing import List, Dict, Any
import numpy as np
import logging

from .base import AudioEffectProcessor
from app.core.errors import AudioProcessingFailedError

logger = logging.getLogger(__name__)


class ReverbProcessor(AudioEffectProcessor):
    """
    High-quality reverb processor using Pedalboard.
    
    Features:
    - Room size control
    - Damping control
    - Wet/dry mix control
    - High-quality convolution-based reverb
    - Real-time processing support
    """
    
    def __init__(self, sample_rate: int = 44100):
        """Initialize reverb processor with Pedalboard."""
        super().__init__(sample_rate)
        
        try:
            from pedalboard import Pedalboard, Reverb
            self.pedalboard = Pedalboard()
            self.reverb_plugin = Reverb()
            self.pedalboard.append(self.reverb_plugin)
            logger.info("Reverb processor initialized with Pedalboard")
        except ImportError:
            logger.error("Pedalboard not available, falling back to basic reverb")
            self.pedalboard = None
            self.reverb_plugin = None
    
    def apply(self, samples: List[float], parameters: Dict[str, Any]) -> List[float]:
        """
        Apply reverb effect to audio samples.
        
        Args:
            samples: Input audio samples
            parameters: Reverb parameters
            
        Returns:
            Processed audio samples with reverb
        """
        try:
            # Validate and normalize parameters
            params = self.validate_parameters(parameters)
            
            # Convert samples to numpy array
            samples_array = self._validate_samples(samples)
            samples_array = self._ensure_mono(samples_array)
            
            if self.pedalboard is not None:
                # Use Pedalboard for high-quality reverb
                return self._apply_pedalboard_reverb(samples_array, params)
            else:
                # Fallback to basic reverb implementation
                return self._apply_basic_reverb(samples_array, params)
                
        except Exception as e:
            logger.error(f"Reverb processing failed: {e}")
            raise AudioProcessingFailedError(
                message=f"Reverb processing failed: {str(e)}",
                error_code="REVERB_PROCESSING_ERROR",
                details={"parameters": parameters}
            )
    
    def _apply_pedalboard_reverb(self, samples: np.ndarray, parameters: Dict[str, Any]) -> List[float]:
        """Apply reverb using Pedalboard library."""
        try:
            # Configure reverb plugin
            self.reverb_plugin.room_size = parameters.get('room_size', 0.5)
            self.reverb_plugin.damping = parameters.get('damping', 0.5)
            self.reverb_plugin.wet_level = parameters.get('wet_level', 0.33)
            self.reverb_plugin.dry_level = parameters.get('dry_level', 0.4)
            self.reverb_plugin.width = parameters.get('width', 1.0)
            
            # Apply reverb
            processed_samples = self.pedalboard.process(samples, self.sample_rate)
            
            # Ensure mono output
            if len(processed_samples.shape) > 1:
                processed_samples = np.mean(processed_samples, axis=1)
            
            # Normalize output
            processed_samples = self._normalize_output(processed_samples)
            
            logger.debug(f"Applied Pedalboard reverb: room_size={parameters.get('room_size')}, "
                        f"damping={parameters.get('damping')}, wet_level={parameters.get('wet_level')}")
            
            return processed_samples.tolist()
            
        except Exception as e:
            logger.error(f"Pedalboard reverb failed: {e}")
            raise AudioProcessingFailedError(
                message=f"Pedalboard reverb processing failed: {str(e)}",
                error_code="PEDALBOARD_REVERB_ERROR"
            )
    
    def _apply_basic_reverb(self, samples: np.ndarray, parameters: Dict[str, Any]) -> List[float]:
        """Apply basic reverb using convolution (fallback method)."""
        try:
            room_size = parameters.get('room_size', 0.5)
            damping = parameters.get('damping', 0.5)
            wet_level = parameters.get('wet_level', 0.33)
            dry_level = parameters.get('dry_level', 0.4)
            
            # Create reverb impulse response
            reverb_length = int(room_size * self.sample_rate * 2)  # 2 seconds max
            reverb_tail = np.exp(-damping * np.arange(reverb_length) / self.sample_rate)
            reverb_tail = reverb_tail / np.sum(reverb_tail)
            
            # Apply convolution
            reverb_signal = np.convolve(samples, reverb_tail, mode='full')
            reverb_signal = reverb_signal[:len(samples)]
            
            # Mix dry and wet signals
            output = dry_level * samples + wet_level * reverb_signal
            
            # Normalize output
            output = self._normalize_output(output)
            
            logger.debug(f"Applied basic reverb: room_size={room_size}, damping={damping}")
            
            return output.tolist()
            
        except Exception as e:
            logger.error(f"Basic reverb failed: {e}")
            raise AudioProcessingFailedError(
                message=f"Basic reverb processing failed: {str(e)}",
                error_code="BASIC_REVERB_ERROR"
            )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize reverb parameters.
        
        Args:
            parameters: Raw parameters
            
        Returns:
            Validated parameters
        """
        validated = {}
        
        # Room size: 0.0 to 1.0
        room_size = parameters.get('room_size', 0.5)
        validated['room_size'] = np.clip(room_size, 0.0, 1.0)
        
        # Damping: 0.0 to 1.0
        damping = parameters.get('damping', 0.5)
        validated['damping'] = np.clip(damping, 0.0, 1.0)
        
        # Wet level: 0.0 to 1.0
        wet_level = parameters.get('wet_level', 0.33)
        validated['wet_level'] = np.clip(wet_level, 0.0, 1.0)
        
        # Dry level: 0.0 to 1.0
        dry_level = parameters.get('dry_level', 0.4)
        validated['dry_level'] = np.clip(dry_level, 0.0, 1.0)
        
        # Width: 0.0 to 1.0 (for stereo effects)
        width = parameters.get('width', 1.0)
        validated['width'] = np.clip(width, 0.0, 1.0)
        
        return validated
    
    def get_default_parameters(self) -> Dict[str, Any]:
        """Get default reverb parameters."""
        return {
            'room_size': 0.5,
            'damping': 0.5,
            'wet_level': 0.33,
            'dry_level': 0.4,
            'width': 1.0
        }
    
    def get_parameter_info(self) -> Dict[str, Any]:
        """Get reverb parameter information."""
        return {
            "name": "Reverb",
            "description": "High-quality reverb effect using Pedalboard",
            "backend": "Pedalboard" if self.pedalboard else "Basic Convolution",
            "parameters": {
                "room_size": {
                    "type": "float",
                    "range": [0.0, 1.0],
                    "default": 0.5,
                    "description": "Size of the reverb room (0.0 = small, 1.0 = large)"
                },
                "damping": {
                    "type": "float",
                    "range": [0.0, 1.0],
                    "default": 0.5,
                    "description": "High-frequency damping (0.0 = bright, 1.0 = dark)"
                },
                "wet_level": {
                    "type": "float",
                    "range": [0.0, 1.0],
                    "default": 0.33,
                    "description": "Level of processed (wet) signal"
                },
                "dry_level": {
                    "type": "float",
                    "range": [0.0, 1.0],
                    "default": 0.4,
                    "description": "Level of original (dry) signal"
                },
                "width": {
                    "type": "float",
                    "range": [0.0, 1.0],
                    "default": 1.0,
                    "description": "Stereo width of the reverb"
                }
            }
        } 