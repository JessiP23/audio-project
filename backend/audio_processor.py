import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AudioProcessor:
    def __init__(self):
        """Initialize the audio processor with default settings."""
        self.sample_rate = 44100
        self.effects = {
            'reverb': self._apply_reverb,
            'delay': self._apply_delay,
            'distortion': self._apply_distortion,
            'filter': self._apply_filter,
            'compression': self._apply_compression,
            'chorus': self._apply_chorus,
            'flanger': self._apply_flanger,
            'phaser': self._apply_phaser,
            'eq': self._apply_equalizer,
            'normalize': self._apply_normalization
        }

    def apply_effect(self, samples: List[float], effect: str, parameters: Dict[str, Any]) -> List[float]:
        """Apply a specified audio effect to the samples."""
        if effect not in self.effects:
            logger.warning(f"Unknown effect: {effect}")
            return samples
        
        try:
            samples_array = np.array(samples, dtype=np.float32)
            processed_samples = self.effects[effect](samples_array, parameters)
            return processed_samples.tolist()
        except Exception as e:
            logger.error(f"Error applying effect {effect}: {e}")
            return samples

    def _apply_reverb(self, samples: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply reverb effect using convolution with impulse response."""
        room_size = parameters.get('room_size', 0.5)
        damping = parameters.get('damping', 0.5)
        
        # Create a simple impulse response
        impulse_length = int(room_size * self.sample_rate)
        impulse = np.exp(-damping * np.arange(impulse_length))
        impulse = impulse / np.sum(impulse)  # Normalize
        
        # Apply convolution
        reverb_samples = signal.convolve(samples, impulse, mode='same')
        
        # Mix dry and wet signals
        dry_wet = parameters.get('dry_wet', 0.5)
        return (1 - dry_wet) * samples + dry_wet * reverb_samples

    def _apply_delay(self, samples: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply delay effect."""
        delay_time = parameters.get('delay_time', 0.1)  # seconds
        feedback = parameters.get('feedback', 0.3)
        mix = parameters.get('mix', 0.5)
        
        delay_samples = int(delay_time * self.sample_rate)
        delayed = np.zeros_like(samples)
        delayed[delay_samples:] = samples[:-delay_samples]
        
        # Apply feedback
        if feedback > 0:
            feedback_samples = np.zeros_like(samples)
            feedback_samples[delay_samples:] = delayed[:-delay_samples] * feedback
            delayed += feedback_samples
        
        return (1 - mix) * samples + mix * delayed

    def _apply_distortion(self, samples: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply distortion effect."""
        drive = parameters.get('drive', 2.0)
        threshold = parameters.get('threshold', 0.5)
        
        # Apply drive
        distorted = samples * drive
        
        # Apply soft clipping
        distorted = np.tanh(distorted)
        
        # Apply threshold
        distorted = np.where(np.abs(distorted) > threshold, 
                           np.sign(distorted) * threshold, 
                           distorted)
        
        return distorted

    def _apply_filter(self, samples: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply low-pass or high-pass filter."""
        filter_type = parameters.get('type', 'lowpass')
        cutoff = parameters.get('cutoff', 1000)  # Hz
        order = parameters.get('order', 4)
        
        # Normalize cutoff frequency
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff / nyquist
        
        if filter_type == 'lowpass':
            b, a = signal.butter(order, normalized_cutoff, btype='low')
        elif filter_type == 'highpass':
            b, a = signal.butter(order, normalized_cutoff, btype='high')
        elif filter_type == 'bandpass':
            low_cutoff = parameters.get('low_cutoff', 500)
            high_cutoff = parameters.get('high_cutoff', 2000)
            b, a = signal.butter(order, [low_cutoff/nyquist, high_cutoff/nyquist], btype='band')
        else:
            return samples
        
        return signal.filtfilt(b, a, samples)

    def _apply_compression(self, samples: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply dynamic range compression."""
        threshold = parameters.get('threshold', -20)  # dB
        ratio = parameters.get('ratio', 4.0)
        attack = parameters.get('attack', 0.01)  # seconds
        release = parameters.get('release', 0.1)  # seconds
        
        # Convert to dB
        threshold_linear = 10**(threshold/20)
        
        # Calculate envelope
        envelope = np.abs(samples)
        
        # Apply attack and release
        attack_samples = int(attack * self.sample_rate)
        release_samples = int(release * self.sample_rate)
        
        # Simple envelope follower
        alpha_attack = 1 - np.exp(-1 / attack_samples)
        alpha_release = 1 - np.exp(-1 / release_samples)
        
        gain_reduction = np.ones_like(samples)
        
        for i in range(1, len(samples)):
            if envelope[i] > threshold_linear:
                # Apply compression
                gain_reduction[i] = (threshold_linear / envelope[i]) ** (1 - 1/ratio)
            else:
                gain_reduction[i] = 1.0
            
            # Smooth gain reduction
            if gain_reduction[i] < gain_reduction[i-1]:
                gain_reduction[i] = (1 - alpha_attack) * gain_reduction[i-1] + alpha_attack * gain_reduction[i]
            else:
                gain_reduction[i] = (1 - alpha_release) * gain_reduction[i-1] + alpha_release * gain_reduction[i]
        
        return samples * gain_reduction

    def _apply_chorus(self, samples: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply chorus effect."""
        rate = parameters.get('rate', 1.5)  # Hz
        depth = parameters.get('depth', 0.002)  # seconds
        mix = parameters.get('mix', 0.5)
        
        # Create LFO for modulation
        t = np.arange(len(samples)) / self.sample_rate
        lfo = depth * np.sin(2 * np.pi * rate * t)
        
        # Apply modulation
        modulated_samples = np.zeros_like(samples)
        for i in range(len(samples)):
            delay_samples = int(lfo[i] * self.sample_rate)
            if i + delay_samples < len(samples):
                modulated_samples[i] = samples[i + delay_samples]
            else:
                modulated_samples[i] = samples[i]
        
        return (1 - mix) * samples + mix * modulated_samples

    def _apply_flanger(self, samples: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply flanger effect."""
        rate = parameters.get('rate', 0.5)  # Hz
        depth = parameters.get('depth', 0.003)  # seconds
        feedback = parameters.get('feedback', 0.3)
        mix = parameters.get('mix', 0.5)
        
        # Create LFO for modulation
        t = np.arange(len(samples)) / self.sample_rate
        lfo = depth * (np.sin(2 * np.pi * rate * t) + 1) / 2  # 0 to depth
        
        # Apply modulation with feedback
        flanged = np.zeros_like(samples)
        for i in range(len(samples)):
            delay_samples = int(lfo[i] * self.sample_rate)
            if i + delay_samples < len(samples):
                flanged[i] = samples[i + delay_samples]
            else:
                flanged[i] = samples[i]
            
            # Add feedback
            if i > 0:
                flanged[i] += feedback * flanged[i-1]
        
        return (1 - mix) * samples + mix * flanged

    def _apply_phaser(self, samples: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply phaser effect."""
        rate = parameters.get('rate', 1.0)  # Hz
        depth = parameters.get('depth', 0.8)
        stages = parameters.get('stages', 4)
        mix = parameters.get('mix', 0.5)
        
        # Create LFO for modulation
        t = np.arange(len(samples)) / self.sample_rate
        lfo = depth * (np.sin(2 * np.pi * rate * t) + 1) / 2
        
        # Apply all-pass filters
        phased = samples.copy()
        for stage in range(stages):
            # All-pass filter coefficients
            freq = 1000 + 4000 * lfo  # Vary frequency from 1kHz to 5kHz
            q = 0.5
            
            for i in range(len(samples)):
                # Simple all-pass filter implementation
                w0 = 2 * np.pi * freq[i] / self.sample_rate
                alpha = np.sin(w0) / (2 * q)
                
                b0 = 1 - alpha
                b1 = -2 * np.cos(w0)
                b2 = 1 + alpha
                a0 = 1 + alpha
                a1 = -2 * np.cos(w0)
                a2 = 1 - alpha
                
                # Apply filter (simplified)
                if i >= 2:
                    phased[i] = (b0 * samples[i] + b1 * samples[i-1] + b2 * samples[i-2] -
                               a1 * phased[i-1] - a2 * phased[i-2]) / a0
        
        return (1 - mix) * samples + mix * phased

    def _apply_equalizer(self, samples: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply multi-band equalizer."""
        bands = parameters.get('bands', {
            'low': {'freq': 100, 'gain': 0, 'q': 1.0},
            'mid': {'freq': 1000, 'gain': 0, 'q': 1.0},
            'high': {'freq': 5000, 'gain': 0, 'q': 1.0}
        })
        
        equalized = samples.copy()
        
        for band_name, band_params in bands.items():
            freq = band_params['freq']
            gain = band_params['gain']
            q = band_params['q']
            
            if gain != 0:
                # Create peaking filter
                w0 = 2 * np.pi * freq / self.sample_rate
                alpha = np.sin(w0) / (2 * q)
                
                # Filter coefficients
                b0 = 1 + alpha * 10**(gain/40)
                b1 = -2 * np.cos(w0)
                b2 = 1 - alpha * 10**(gain/40)
                a0 = 1 + alpha / 10**(gain/40)
                a1 = -2 * np.cos(w0)
                a2 = 1 - alpha / 10**(gain/40)
                
                # Apply filter
                equalized = signal.filtfilt([b0, b1, b2], [a0, a1, a2], equalized)
        
        return equalized

    def _apply_normalization(self, samples: np.ndarray, parameters: Dict[str, Any]) -> np.ndarray:
        """Apply normalization to audio samples."""
        target_rms = parameters.get('target_rms', 0.1)
        
        # Calculate current RMS
        current_rms = np.sqrt(np.mean(samples**2))
        
        if current_rms > 0:
            # Calculate gain
            gain = target_rms / current_rms
            return samples * gain
        
        return samples

    def load_audio_file(self, file_path: str) -> List[float]:
        """Load an audio file and return samples."""
        try:
            # Load audio file
            samples, sample_rate = librosa.load(file_path, sr=self.sample_rate)
            
            # Convert to mono if stereo
            if len(samples.shape) > 1:
                samples = np.mean(samples, axis=1)
            
            return samples.tolist()
        
        except Exception as e:
            logger.error(f"Error loading audio file {file_path}: {e}")
            return []

    def save_audio_file(self, samples: List[float], file_path: str) -> bool:
        """Save audio samples to a file."""
        try:
            samples_array = np.array(samples, dtype=np.float32)
            sf.write(file_path, samples_array, self.sample_rate)
            return True
        except Exception as e:
            logger.error(f"Error saving audio file {file_path}: {e}")
            return False

    def analyze_audio(self, samples: List[float]) -> Dict[str, Any]:
        """Analyze audio characteristics."""
        samples_array = np.array(samples, dtype=np.float32)
        
        analysis = {
            'rms': float(np.sqrt(np.mean(samples_array**2))),
            'peak': float(np.max(np.abs(samples_array))),
            'dynamic_range': float(np.max(samples_array) - np.min(samples_array)),
            'zero_crossings': int(np.sum(np.diff(np.sign(samples_array)) != 0)),
            'spectral_centroid': float(librosa.feature.spectral_centroid(y=samples_array, sr=self.sample_rate).mean()),
            'spectral_rolloff': float(librosa.feature.spectral_rolloff(y=samples_array, sr=self.sample_rate).mean())
        }
        
        return analysis 