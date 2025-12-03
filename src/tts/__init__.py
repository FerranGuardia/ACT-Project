"""
TTS module - Text-to-Speech conversion.

Provides text-to-speech functionality using Edge-TTS.
"""

from .tts_engine import TTSEngine
from .voice_manager import VoiceManager
from .text_cleaner import clean_text_for_tts
from .ssml_builder import build_ssml, parse_rate, parse_pitch, parse_volume

__all__ = [
    "TTSEngine",
    "VoiceManager",
    "clean_text_for_tts",
    "build_ssml",
    "parse_rate",
    "parse_pitch",
    "parse_volume",
]
