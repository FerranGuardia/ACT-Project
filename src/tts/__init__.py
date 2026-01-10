"""
TTS module - Text-to-Speech conversion.

Provides text-to-speech functionality using Edge-TTS.
"""

from .audio_merger import AudioMerger
from .ssml_builder import build_ssml, parse_pitch, parse_rate, parse_volume
from text_utils import clean_text_for_tts
from .text_processor import TextProcessor
from .tts_engine import TTSEngine, format_chapter_intro
from .voice_manager import VoiceManager
from .voice_validator import VoiceValidator

__all__ = [
    "TTSEngine",
    "VoiceManager",
    "clean_text_for_tts",
    "build_ssml",
    "parse_rate",
    "parse_pitch",
    "parse_volume",
    "format_chapter_intro",
    "VoiceValidator",
    "TextProcessor",
    "AudioMerger",
]
