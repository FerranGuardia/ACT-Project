"""
Voice manager for TTS module.

Handles loading, caching, and managing TTS voices from multiple providers.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.config_manager import get_config
from core.logger import get_logger
from tts.providers.provider_manager import TTSProviderManager

logger = get_logger("tts.voice_manager")


class VoiceManager:
    """Manages TTS voices from multiple providers with caching support."""

    def __init__(self, cache_duration_days: int = 7, provider_manager: Optional[TTSProviderManager] = None):
        """
        Initialize voice manager.

        Args:
            cache_duration_days: How long to keep cached voices (default: 7 days)
            provider_manager: Optional TTSProviderManager instance. If None, creates a new one.
        """
        self.cache_duration = cache_duration_days * 24 * 3600  # Convert to seconds
        self.config = get_config()
        
        # Initialize provider manager
        self.provider_manager = provider_manager or TTSProviderManager()
        
        # Cache file location
        cache_dir = Path.home() / ".act" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = cache_dir / "voices_cache.json"
        
        self._voices: List[Dict[str, Any]] = []
        self._voices_loaded = False

    def get_voices(self, locale: Optional[str] = None, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get available voices, optionally filtered by locale and provider.

        Args:
            locale: Locale filter (e.g., "en-US"). Defaults to "en-US" only.
            provider: Optional provider name ("edge_tts" or "pyttsx3"). 
                     If None, returns voices from all providers.

        Returns:
            List of voice dictionaries with keys: id, name, language, gender, quality, provider
        """
        # Default to en-US only as per requirements
        if locale is None:
            locale = "en-US"
        
        # If provider is specified, get voices from that provider only
        # ProviderManager returns List[Dict] without type args, but we know it's List[Dict[str, Any]]
        if provider:
            voices = self.provider_manager.get_voices_by_provider(provider, locale=locale)  # type: ignore[assignment]
        else:
            # Get voices from all providers
            voices = self.provider_manager.get_all_voices(locale=locale)  # type: ignore[assignment]
        
        # Cast to proper type since ProviderManager returns List[Dict] without type args
        return voices  # type: ignore[return-value]

    def get_voice_list(self, locale: Optional[str] = None, provider: Optional[str] = None) -> List[str]:
        """
        Get list of voice names formatted for display.

        Args:
            locale: Locale filter (e.g., "en-US"). Defaults to "en-US" only.
            provider: Optional provider name ("edge_tts" or "pyttsx3").
                     If None, returns voices from all providers.

        Returns:
            List of formatted voice strings: "name - gender"
        """
        voices = self.get_voices(locale=locale, provider=provider)
        # Handle both old format (ShortName) and new format (name)
        result: List[str] = []
        for v in voices:
            # Type ignore because v is Dict[str, Any] but Pylance sees Dict[Unknown, Unknown]
            name_raw = v.get("name") or v.get("ShortName", "Unknown")  # type: ignore[arg-type]
            name = str(name_raw) if name_raw is not None else "Unknown"
            gender_raw = v.get("gender", "") or v.get("Gender", "")  # type: ignore[arg-type]
            gender = str(gender_raw).capitalize() if gender_raw else ""
            result.append(f"{name} - {gender}")
        return result

    def get_voice_by_name(self, voice_name: str, provider: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get voice dictionary by name or ID.

        Args:
            voice_name: Voice name or ID (e.g., "en-US-AndrewNeural" or voice name)
            provider: Optional provider name to search within

        Returns:
            Voice dictionary or None if not found
        """
        voices = self.get_voices(provider=provider)
        voice_name_lower = voice_name.lower().strip()
        
        for voice in voices:
            # Check exact matches first
            voice_id = (voice.get("id") or "").lower()
            voice_name_full = (voice.get("name") or "").lower()
            voice_short = (voice.get("ShortName") or "").lower()
            
            if (voice_id == voice_name_lower or 
                voice_name_full == voice_name_lower or 
                voice_short == voice_name_lower):
                return voice
            
            # Check partial matches (for pyttsx3 voices like "Microsoft David Desktop" matching "Microsoft David Desktop - English (United States)")
            if voice_name_lower in voice_name_full or voice_name_full.startswith(voice_name_lower):
                return voice
        
        return None
    
    def get_providers(self) -> List[str]:
        """
        Get list of available provider names.

        Returns:
            List of provider names (e.g., ["edge_tts", "pyttsx3"])
        """
        return self.provider_manager.get_providers()
    
    def get_voices_by_provider(self, provider: str, locale: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get voices from a specific provider.

        Args:
            provider: Provider name ("edge_tts" or "pyttsx3")
            locale: Optional locale filter (e.g., "en-US"). Defaults to "en-US" only.

        Returns:
            List of voice dictionaries from the specified provider
        """
        if locale is None:
            locale = "en-US"
        # ProviderManager returns List[Dict] without type args, but we know it's List[Dict[str, Any]]
        return self.provider_manager.get_voices_by_provider(provider, locale=locale)  # type: ignore[return-value]

    def _load_voices(self) -> None:
        """Load voices from cache or providers (legacy method for backward compatibility)."""
        # Try cache first
        cached_voices = self._load_cache()
        if cached_voices:
            self._voices = cached_voices
            self._voices_loaded = True
            logger.info(f"Loaded {len(cached_voices)} voices from cache")
            return

        # Load from providers using ProviderManager
        logger.info("Loading voices from TTS providers...")
        try:
            # ProviderManager returns List[Dict] without type args, but we know it's List[Dict[str, Any]]
            voices = self.provider_manager.get_all_voices(locale="en-US")  # type: ignore[assignment]
            
            # Convert to legacy format for backward compatibility
            legacy_voices: List[Dict[str, Any]] = []
            for voice in voices:
                # Type ignore because voice is Dict[str, Any] but Pylance sees Dict[Unknown, Unknown]
                id_raw = voice.get("id", "")  # type: ignore[arg-type]
                name_raw = voice.get("name", "")  # type: ignore[arg-type]
                language_raw = voice.get("language", "en-US")  # type: ignore[arg-type]
                gender_raw = voice.get("gender", "neutral")  # type: ignore[arg-type]
                
                legacy_voice: Dict[str, Any] = {
                    "ShortName": str(id_raw) if id_raw is not None else "",
                    "FriendlyName": str(name_raw) if name_raw is not None else "",
                    "Locale": str(language_raw) if language_raw is not None else "en-US",
                    "Gender": str(gender_raw).capitalize() if gender_raw else "Neutral",
                    "Name": str(name_raw) if name_raw is not None else "",
                }
                legacy_voices.append(legacy_voice)
            
            # Sort by ShortName
            legacy_voices.sort(key=lambda x: str(x.get("ShortName", "")) if isinstance(x, dict) else "")  # type: ignore[arg-type]
            self._voices = legacy_voices
            self._voices_loaded = True
            
            # Save to cache
            self._save_cache(legacy_voices)
            
            logger.info(f"Loaded {len(legacy_voices)} voices from providers")
        except Exception as e:
            logger.error(f"Error loading voices: {e}")
            self._voices = []
            self._voices_loaded = True

    def refresh_voices(self) -> None:
        """Refresh voices list from providers and update cache."""
        logger.info("Refreshing voices from TTS providers...")
        try:
            # ProviderManager returns List[Dict] without type args, but we know it's List[Dict[str, Any]]
            voices = self.provider_manager.get_all_voices(locale="en-US")  # type: ignore[assignment]
            
            # Convert to legacy format for backward compatibility
            legacy_voices: List[Dict[str, Any]] = []
            for voice in voices:
                # Type ignore because voice is Dict[str, Any] but Pylance sees Dict[Unknown, Unknown]
                id_raw = voice.get("id", "")  # type: ignore[arg-type]
                name_raw = voice.get("name", "")  # type: ignore[arg-type]
                language_raw = voice.get("language", "en-US")  # type: ignore[arg-type]
                gender_raw = voice.get("gender", "neutral")  # type: ignore[arg-type]
                
                legacy_voice: Dict[str, Any] = {
                    "ShortName": str(id_raw) if id_raw is not None else "",
                    "FriendlyName": str(name_raw) if name_raw is not None else "",
                    "Locale": str(language_raw) if language_raw is not None else "en-US",
                    "Gender": str(gender_raw).capitalize() if gender_raw else "Neutral",
                    "Name": str(name_raw) if name_raw is not None else "",
                }
                legacy_voices.append(legacy_voice)
            
            # Sort by ShortName
            legacy_voices.sort(key=lambda x: str(x.get("ShortName", "")) if isinstance(x, dict) else "")  # type: ignore[arg-type]
            self._voices = legacy_voices
            self._voices_loaded = True
            
            # Update cache
            self._save_cache(legacy_voices)
            
            logger.info(f"Refreshed {len(legacy_voices)} voices")
        except Exception as e:
            logger.error(f"Error refreshing voices: {e}")

    def _load_cache(self) -> Optional[List[Dict[str, Any]]]:
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

    def _save_cache(self, voices: List[Dict[str, Any]]) -> None:
        """Save voices to cache."""
        try:
            cache_data: Dict[str, Any] = {
                "timestamp": time.time(),
                "voices": voices
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
            logger.debug(f"Saved {len(voices)} voices to cache")
        except Exception as e:
            logger.warning(f"Error saving voice cache: {e}")

