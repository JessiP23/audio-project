"""
Audio Processor Package for the Audio Processing Backend.
Provides a unified interface for all audio effects and processing.
"""

from .base import AudioEffectProcessor, AudioProcessorFactory
from .reverb import ReverbProcessor

# Register all available effects
AudioProcessorFactory.register("reverb", ReverbProcessor)

# Import other effects as they are created
# from .delay import DelayProcessor
# from .distortion import DistortionProcessor
# from .filter import FilterProcessor
# from .compression import CompressionProcessor
# from .chorus import ChorusProcessor
# from .flanger import FlangerProcessor
# from .phaser import PhaserProcessor
# from .equalizer import EqualizerProcessor
# from .normalize import NormalizeProcessor

# AudioProcessorFactory.register("delay", DelayProcessor)
# AudioProcessorFactory.register("distortion", DistortionProcessor)
# AudioProcessorFactory.register("filter", FilterProcessor)
# AudioProcessorFactory.register("compression", CompressionProcessor)
# AudioProcessorFactory.register("chorus", ChorusProcessor)
# AudioProcessorFactory.register("flanger", FlangerProcessor)
# AudioProcessorFactory.register("phaser", PhaserProcessor)
# AudioProcessorFactory.register("equalizer", EqualizerProcessor)
# AudioProcessorFactory.register("normalize", NormalizeProcessor)

__all__ = [
    "AudioEffectProcessor",
    "AudioProcessorFactory",
    "ReverbProcessor",
] 