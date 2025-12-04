"""
TTS Engine - Main text-to-speech conversion engine.

Handles conversion of text to audio files using Edge-TTS.
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable

from core.config_manager import get_config
from core.logger import get_logger

from .voice_manager import VoiceManager
from .text_cleaner import clean_text_for_tts
from .ssml_builder import build_ssml, parse_rate, parse_pitch, parse_volume

logger = get_logger("tts.tts_engine")


class TTSEngine:
    """Main TTS engine for converting text to speech."""

    def __init__(self, base_text_cleaner: Optional[Callable[[str], str]] = None):
        """
        Initialize TTS engine.

        Args:
            base_text_cleaner: Optional function to clean text before TTS cleaning
                               (e.g., scraper text cleaner)
        """
        self.config = get_config()
        self.voice_manager = VoiceManager()
        self.base_text_cleaner = base_text_cleaner

    def get_available_voices(self, locale: Optional[str] = None) -> list:
        """
        Get list of available voices.

        Args:
            locale: Optional locale filter (e.g., "en-US")

        Returns:
            List of voice dictionaries
        """
        return self.voice_manager.get_voices(locale)

    def get_voice_list(self, locale: Optional[str] = None) -> list:
        """
        Get formatted list of voices for display.

        Args:
            locale: Optional locale filter (e.g., "en-US")

        Returns:
            List of formatted voice strings
        """
        return self.voice_manager.get_voice_list(locale)

    def convert_text_to_speech(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """
        Convert text to speech and save as audio file.

        Args:
            text: Text to convert
            output_path: Path where audio file will be saved
            voice: Voice short name (e.g., "en-US-AndrewNeural"). 
                   If None, uses default from config
            rate: Speech rate (-50 to 100). If None, uses config
            pitch: Pitch adjustment (-50 to 50). If None, uses config
            volume: Volume adjustment (-50 to 50). If None, uses config

        Returns:
            True if successful, False otherwise
        """
        try:
            # Import edge_tts (lazy import)
            import edge_tts
        except ImportError:
            logger.error("edge-tts not installed. Install with: pip install edge-tts")
            return False

        # Get voice
        if voice is None:
            voice = self.config.get("tts.voice", "en-US-AndrewNeural")
        
        # Verify voice exists
        voice_dict = self.voice_manager.get_voice_by_name(voice)
        if not voice_dict:
            logger.warning(f"Voice '{voice}' not found, using default")
            voice = "en-US-AndrewNeural"

        # Get rate, pitch, volume from config if not provided
        if rate is None:
            rate_str = self.config.get("tts.rate", "+0%")
            rate = parse_rate(rate_str)
        
        if pitch is None:
            pitch_str = self.config.get("tts.pitch", "+0Hz")
            pitch = parse_pitch(pitch_str)
        
        if volume is None:
            volume_str = self.config.get("tts.volume", "+0%")
            volume = parse_volume(volume_str)

        # Clean text for TTS
        cleaned_text = clean_text_for_tts(text, self.base_text_cleaner)

        # Build SSML
        ssml_text = build_ssml(cleaned_text, rate=rate, pitch=pitch, volume=volume)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to speech
        logger.info(f"Converting text to speech: {output_path.name}")
        logger.debug(f"Voice: {voice}, Rate: {rate}%, Pitch: {pitch}%, Volume: {volume}%")

        try:
            # Run async conversion
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            communicate = edge_tts.Communicate(text=ssml_text, voice=voice)
            loop.run_until_complete(communicate.save(str(output_path)))
            loop.close()
            
            logger.info(f"✓ Created audio file: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error converting text to speech: {e}")
            return False

    def convert_file_to_speech(
        self,
        input_file: Path,
        output_path: Optional[Path] = None,
        voice: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """
        Convert text file to speech.

        Args:
            input_file: Path to text file
            output_path: Path for output audio file. If None, uses input filename with .mp3
            voice: Voice short name. If None, uses config
            rate: Speech rate. If None, uses config
            pitch: Pitch adjustment. If None, uses config
            volume: Volume adjustment. If None, uses config

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read text file
            with open(input_file, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Error reading input file {input_file}: {e}")
            return False

        # Determine output path
        if output_path is None:
            output_path = input_file.with_suffix(".mp3")

        # Convert to speech
        return self.convert_text_to_speech(
            text=text,
            output_path=output_path,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume=volume
        )

