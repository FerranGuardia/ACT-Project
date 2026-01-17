"""
Standalone TTS service with a clean public API.
"""

from pathlib import Path
from typing import List, Optional

from core.logger import get_logger
from tts import TTSEngine, VoiceManager

logger = get_logger("services.tts_service")


class TTSService:
    """Standalone TTS service for conversion and voice discovery."""

    def __init__(self):
        self._engine = TTSEngine()
        self._voice_manager = VoiceManager()

    def get_providers(self) -> List[str]:
        """Return available provider names."""
        return self._voice_manager.get_providers()

    def get_voice_list(self, locale: Optional[str] = None, provider: Optional[str] = None) -> List[str]:
        """Return formatted voice display names."""
        return self._voice_manager.get_voice_list(locale=locale, provider=provider)

    def convert_text(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None,
        provider: Optional[str] = None
    ) -> bool:
        """Convert text to speech and save to output_path."""
        return self._engine.convert_text_to_speech(
            text=text,
            output_path=output_path,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume,
            provider=provider
        )


__all__ = ["TTSService"]
