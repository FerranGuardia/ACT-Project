"""
Voice manager for TTS module.

Handles loading, caching, and managing Edge-TTS voices.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from core.config_manager import get_config
from core.logger import get_logger

logger = get_logger("tts.voice_manager")


class VoiceManager:
    """Manages Edge-TTS voices with caching support."""

    def __init__(self, cache_duration_days: int = 7):
        """
        Initialize voice manager.

        Args:
            cache_duration_days: How long to keep cached voices (default: 7 days)
        """
        self.cache_duration = cache_duration_days * 24 * 3600  # Convert to seconds
        self.config = get_config()
        
        # Cache file location
        cache_dir = Path.home() / ".act" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / "voices_cache.json"
        
        self._voices: List[Dict] = []
        self._voices_loaded = False

    def get_voices(self, locale: Optional[str] = None) -> List[Dict]:
        """
        Get available voices, optionally filtered by locale.

        Args:
            locale: Locale filter (e.g., "en-US"). If None, returns all voices.

        Returns:
            List of voice dictionaries
        """
        if not self._voices_loaded:
            self._load_voices()
        
        if locale:
            return [v for v in self._voices if v.get("Locale") == locale]
        return self._voices.copy()

    def get_voice_list(self, locale: Optional[str] = None) -> List[str]:
        """
        Get list of voice names formatted for display.

        Args:
            locale: Locale filter (e.g., "en-US"). If None, returns all voices.

        Returns:
            List of formatted voice strings: "ShortName - Gender"
        """
        voices = self.get_voices(locale)
        return [f"{v['ShortName']} - {v['Gender']}" for v in voices]

    def get_voice_by_name(self, voice_name: str) -> Optional[Dict]:
        """
        Get voice dictionary by short name.

        Args:
            voice_name: Voice short name (e.g., "en-US-AndrewNeural")

        Returns:
            Voice dictionary or None if not found
        """
        voices = self.get_voices()
        for voice in voices:
            if voice.get("ShortName") == voice_name:
                return voice
        return None

    def _load_voices(self) -> None:
        """Load voices from cache or Edge-TTS API."""
        # Try cache first
        cached_voices = self._load_cache()
        if cached_voices:
            self._voices = cached_voices
            self._voices_loaded = True
            logger.info(f"Loaded {len(cached_voices)} voices from cache")
            return

        # Load from API
        logger.info("Loading voices from Edge-TTS API...")
        try:
            import edge_tts
            
            # Run async function in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            voices = loop.run_until_complete(edge_tts.list_voices())
            loop.close()
            
            # Sort by ShortName
            voices.sort(key=lambda x: x.get("ShortName", ""))
            self._voices = voices
            self._voices_loaded = True
            
            # Save to cache
            self._save_cache(voices)
            
            logger.info(f"Loaded {len(voices)} voices from API")
        except ImportError:
            logger.error("edge-tts not installed. Install with: pip install edge-tts")
            self._voices = []
            self._voices_loaded = True
        except Exception as e:
            logger.error(f"Error loading voices: {e}")
            self._voices = []
            self._voices_loaded = True

    def refresh_voices(self) -> None:
        """Refresh voices list from API and update cache."""
        logger.info("Refreshing voices from Edge-TTS API...")
        try:
            import edge_tts
            
            # Run async function in new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            voices = loop.run_until_complete(edge_tts.list_voices())
            loop.close()
            
            # Sort by ShortName
            voices.sort(key=lambda x: x.get("ShortName", ""))
            self._voices = voices
            self._voices_loaded = True
            
            # Update cache
            self._save_cache(voices)
            
            logger.info(f"Refreshed {len(voices)} voices")
        except ImportError:
            logger.error("edge-tts not installed. Install with: pip install edge-tts")
        except Exception as e:
            logger.error(f"Error refreshing voices: {e}")

    def _load_cache(self) -> Optional[List[Dict]]:
        """Load voices from cache if valid."""
        try:
            if not self.cache_file.exists():
                return None

            with open(self.cache_file, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                cache_time = cached_data.get("timestamp", 0)
                
                # Check if cache is still valid
                if time.time() - cache_time < self.cache_duration:
                    return cached_data.get("voices", [])
                
                logger.debug("Voice cache expired")
                return None
        except Exception as e:
            logger.warning(f"Error loading voice cache: {e}")
            return None

    def _save_cache(self, voices: List[Dict]) -> None:
        """Save voices to cache."""
        try:
            cache_data = {
                "timestamp": time.time(),
                "voices": voices
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Saved {len(voices)} voices to cache")
        except Exception as e:
            logger.warning(f"Error saving voice cache: {e}")

