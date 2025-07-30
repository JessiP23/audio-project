import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from scipy.fft import fft, ifft
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Advanced audio processor with effects and analysis capabilities."""
    
    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.effects_chain = []
        
    def apply_effect(self, samples: List[float], effect: str, parameters: Dict[str, Any]) -> List[float]:
        """Apply audio effect to samples."""
        logger.debug(f"Applying effect '{effect}' to {len(samples)} samples")
        logger.debug(f"Effect parameters: {parameters}")
        
        try:
            samples_array = np.array(samples, dtype=np.float32)
            logger.debug(f"Converted samples to numpy array with shape: {samples_array.shape}")
            
            if effect == "reverb":
                logger.debug("Applying reverb effect")
                return self._apply_reverb(samples_array, parameters)
            elif effect == "delay":
                logger.debug("Applying delay effect")
                return self._apply_delay(samples_array, parameters)
            elif effect == "distortion":
                logger.debug("Applying distortion effect")
                return self._apply_distortion(samples_array, parameters)
            elif effect == "filter":
                logger.debug("Applying filter effect")
                return self._apply_filter(samples_array, parameters)
            elif effect == "compression":
                logger.debug("Applying compression effect")
                return self._apply_compression(samples_array, parameters)
            elif effect == "chorus":
                logger.debug("Applying chorus effect")
                return self._apply_chorus(samples_array, parameters)
            elif effect == "flanger":
                logger.debug("Applying flanger effect")
                return self._apply_flanger(samples_array, parameters)
            elif effect == "phaser":
                logger.debug("Applying phaser effect")
                return self._apply_phaser(samples_array, parameters)
            elif effect == "equalizer":
                logger.debug("Applying equalizer effect")
                return self._apply_equalizer(samples_array, parameters)
            elif effect == "normalize":
                logger.debug("Applying normalization effect")
                return self._apply_normalization(samples_array, parameters)
            else:
                logger.warning(f"Unknown effect: {effect}")
                return samples
                
        except Exception as e:
            logger.error(f"Error applying {effect}: {e}")
            logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return samples
    
    def _apply_reverb(self, samples: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply reverb effect."""
        room_size = params.get('room_size', 0.5)
        damping = params.get('damping', 0.5)
        
        # Simple convolution-based reverb
        reverb_length = int(room_size * self.sample_rate)
        reverb_tail = np.exp(-damping * np.arange(reverb_length) / self.sample_rate)
        reverb_tail = reverb_tail / np.sum(reverb_tail)
        
        # Apply convolution
        reverb_signal = np.convolve(samples, reverb_tail, mode='full')
        reverb_signal = reverb_signal[:len(samples)]
        
        # Mix dry and wet signals
        wet_level = room_size
        dry_level = 1.0 - wet_level
        
        return dry_level * samples + wet_level * reverb_signal
    
    def _apply_delay(self, samples: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply delay effect."""
        delay_time = params.get('delay_time', 0.3)
        feedback = params.get('feedback', 0.3)
        
        delay_samples = int(delay_time * self.sample_rate)
        output = np.copy(samples)
        
        # Add delayed signal with feedback
        for i in range(len(samples) - delay_samples):
            output[i + delay_samples] += feedback * output[i]
        
        return output
    
    def _apply_distortion(self, samples: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply distortion effect."""
        drive = params.get('drive', 0.5)
        
        # Soft clipping distortion
        distorted = samples * (1 + drive * 10)
        return np.tanh(distorted)
    
    def _apply_filter(self, samples: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply low-pass filter."""
        cutoff = params.get('cutoff', 1000)
        resonance = params.get('resonance', 0.5)
        
        # Design Butterworth filter
        nyquist = self.sample_rate / 2
        normalized_cutoff = cutoff / nyquist
        b, a = signal.butter(4, normalized_cutoff, btype='low')
        
        return signal.filtfilt(b, a, samples)
    
    def _apply_compression(self, samples: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply dynamic range compression."""
        threshold = params.get('threshold', -20)
        ratio = params.get('ratio', 4)
        
        # Convert threshold to linear scale
        threshold_linear = 10 ** (threshold / 20)
        
        # Calculate compression
        compressed = np.copy(samples)
        for i in range(len(samples)):
            if abs(samples[i]) > threshold_linear:
                if samples[i] > 0:
                    compressed[i] = threshold_linear + (samples[i] - threshold_linear) / ratio
                else:
                    compressed[i] = -threshold_linear + (samples[i] + threshold_linear) / ratio
        
        return compressed
    
    def _apply_chorus(self, samples: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply chorus effect."""
        rate = params.get('rate', 1.5)
        depth = params.get('depth', 0.002)
        
        # Create modulated delay
        t = np.arange(len(samples)) / self.sample_rate
        modulation = depth * np.sin(2 * np.pi * rate * t)
        
        output = np.copy(samples)
        for i in range(len(samples)):
            delay_samples = int(modulation[i] * self.sample_rate)
            if i + delay_samples < len(samples):
                output[i] += 0.5 * samples[i + delay_samples]
        
        return output
    
    def _apply_flanger(self, samples: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply flanger effect."""
        rate = params.get('rate', 0.5)
        depth = params.get('depth', 0.005)
        
        # Create modulated delay
        t = np.arange(len(samples)) / self.sample_rate
        modulation = depth * np.sin(2 * np.pi * rate * t)
        
        output = np.copy(samples)
        for i in range(len(samples)):
            delay_samples = int(modulation[i] * self.sample_rate)
            if i + delay_samples < len(samples):
                output[i] += samples[i + delay_samples]
        
        return output * 0.5
    
    def _apply_phaser(self, samples: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply phaser effect."""
        rate = params.get('rate', 1.0)
        depth = params.get('depth', 0.5)
        
        # Create all-pass filter modulation
        t = np.arange(len(samples)) / self.sample_rate
        modulation = depth * np.sin(2 * np.pi * rate * t)
        
        output = np.copy(samples)
        for i in range(len(samples)):
            # Simple all-pass filter
            freq = 1000 + 500 * modulation[i]
            b = [1, -2 * np.cos(2 * np.pi * freq / self.sample_rate), 1]
            a = [1, -2 * np.cos(2 * np.pi * freq / self.sample_rate) * 0.9, 0.9]
            
            if i >= 2:
                output[i] = b[0] * samples[i] + b[1] * samples[i-1] + b[2] * samples[i-2] - a[1] * output[i-1] - a[2] * output[i-2]
        
        return output
    
    def _apply_equalizer(self, samples: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply multi-band equalizer."""
        bands = params.get('bands', {
            'low': {'freq': 100, 'gain': 0},
            'mid': {'freq': 1000, 'gain': 0},
            'high': {'freq': 5000, 'gain': 0}
        })
        
        output = np.zeros_like(samples)
        
        for band_name, band_params in bands.items():
            freq = band_params['freq']
            gain = band_params['gain']
            
            # Design band-pass filter
            nyquist = self.sample_rate / 2
            normalized_freq = freq / nyquist
            b, a = signal.butter(2, normalized_freq, btype='low')
            
            filtered = signal.filtfilt(b, a, samples)
            output += filtered * (10 ** (gain / 20))
        
        return output
    
    def _apply_normalization(self, samples: np.ndarray, params: Dict[str, Any]) -> np.ndarray:
        """Apply normalization."""
        target_level = params.get('target_level', -1.0)
        
        # Find peak level
        peak_level = np.max(np.abs(samples))
        if peak_level > 0:
            # Calculate scaling factor
            target_linear = 10 ** (target_level / 20)
            scale_factor = target_linear / peak_level
            
            # Apply scaling and ensure we don't exceed 1.0
            normalized = samples * scale_factor
            return np.clip(normalized, -1.0, 1.0)
        
        return samples
    
    def load_audio_file(self, file_path: str) -> List[float]:
        """Load audio file and return samples."""
        try:
            # Load audio file
            samples, sr = librosa.load(file_path, sr=self.sample_rate)
            
            # Convert to mono if stereo
            if len(samples.shape) > 1:
                samples = np.mean(samples, axis=1)
            
            return samples.tolist()
            
        except Exception as e:
            logger.error(f"Error loading audio file {file_path}: {e}")
            return []
    
    def save_audio_file(self, samples: List[float], file_path: str) -> bool:
        """Save samples to audio file."""
        try:
            samples_array = np.array(samples, dtype=np.float32)
            sf.write(file_path, samples_array, self.sample_rate)
            return True
        except Exception as e:
            logger.error(f"Error saving audio file {file_path}: {e}")
            return False
    
    def analyze_audio(self, samples: List[float]) -> Dict[str, Any]:
        """Analyze audio characteristics."""
        try:
            samples_array = np.array(samples, dtype=np.float32)
            
            # Basic analysis
            rms = np.sqrt(np.mean(samples_array**2))
            peak = np.max(np.abs(samples_array))
            
            # Spectral analysis
            if len(samples_array) > 0:
                # FFT for spectral analysis
                fft_vals = np.abs(fft(samples_array))
                freqs = np.fft.fftfreq(len(samples_array), 1/self.sample_rate)
                
                # Spectral centroid
                spectral_centroid = np.sum(freqs * fft_vals) / np.sum(fft_vals)
                
                # Spectral rolloff
                cumulative_sum = np.cumsum(fft_vals)
                rolloff_threshold = 0.85 * cumulative_sum[-1]
                spectral_rolloff = freqs[np.where(cumulative_sum >= rolloff_threshold)[0][0]]
                
                # Zero crossing rate
                zero_crossings = np.sum(np.diff(np.sign(samples_array)) != 0)
                zero_crossing_rate = zero_crossings / len(samples_array)
                
            else:
                spectral_centroid = 0
                spectral_rolloff = 0
                zero_crossing_rate = 0
            
            return {
                'rms': float(rms),
                'peak': float(peak),
                'spectral_centroid': float(spectral_centroid),
                'spectral_rolloff': float(spectral_rolloff),
                'zero_crossing_rate': float(zero_crossing_rate),
                'duration': len(samples) / self.sample_rate,
                'sample_rate': self.sample_rate
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audio: {e}")
            return {}
    
    def extract_features(self, samples: List[float]) -> Dict[str, Any]:
        """Extract advanced audio features for AI/ML applications."""
        try:
            samples_array = np.array(samples, dtype=np.float32)
            
            if len(samples_array) == 0:
                return {}
            
            # MFCC features (commonly used in speech recognition)
            mfccs = librosa.feature.mfcc(y=samples_array, sr=self.sample_rate, n_mfcc=13)
            mfcc_mean = np.mean(mfccs, axis=1)
            mfcc_std = np.std(mfccs, axis=1)
            
            # Chroma features (for musical analysis)
            chroma = librosa.feature.chroma_stft(y=samples_array, sr=self.sample_rate)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=samples_array, sr=self.sample_rate)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=samples_array, sr=self.sample_rate)[0]
            
            # Tempo and beat features
            tempo, _ = librosa.beat.beat_track(y=samples_array, sr=self.sample_rate)
            
            # Harmonic features
            harmonic, percussive = librosa.effects.hpss(samples_array)
            harmonic_ratio = np.sum(harmonic**2) / (np.sum(harmonic**2) + np.sum(percussive**2))
            
            return {
                'mfcc_mean': mfcc_mean.tolist(),
                'mfcc_std': mfcc_std.tolist(),
                'chroma_mean': chroma_mean.tolist(),
                'spectral_centroids_mean': float(np.mean(spectral_centroids)),
                'spectral_rolloff_mean': float(np.mean(spectral_rolloff)),
                'tempo': float(tempo),
                'harmonic_ratio': float(harmonic_ratio),
                'duration': len(samples) / self.sample_rate
            }
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return {} 