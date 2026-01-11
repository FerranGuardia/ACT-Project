"""
TTS module - Text-to-Speech conversion.

Provides text-to-speech functionality using Edge-TTS with a new modular architecture.
"""

# Main public API
from .conversion_coordinator import TTSConversionCoordinator
from .tts_engine import TTSEngine, format_chapter_intro

# Supporting classes (may be useful for advanced users)
from .voice_resolver import VoiceResolver
from .voice_manager import VoiceManager
from .text_processing_pipeline import TextProcessingPipeline
from .resource_manager import TTSResourceManager
from .conversion_strategies import ConversionStrategySelector

# Provider management
from .providers.provider_manager import TTSProviderManager

# Legacy components (still available for compatibility)
from .audio_merger import AudioMerger
from .ssml_builder import build_ssml, parse_pitch, parse_rate, parse_volume
from text_utils import clean_text_for_tts

__all__ = [
    # Main API
    "TTSEngine",
    "TTSConversionCoordinator",
    "format_chapter_intro",

    # Supporting classes
    "VoiceResolver",
    "VoiceManager",
    "TextProcessingPipeline",
    "ResourceManager",
    "ConversionStrategySelector",

    # Provider management
    "TTSProviderManager",

    # Utilities
    "clean_text_for_tts",
    "build_ssml",
    "parse_rate",
    "parse_pitch",
    "parse_volume",

    # Legacy
    "AudioMerger",
]
