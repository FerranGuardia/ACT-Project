"""
TTS Provider Manager

Manages multiple TTS providers and implements fallback logic.
Tries Edge TTS first (cloud, high quality), falls back to pyttsx3 (offline).
"""

from pathlib import Path
from typing import List, Dict, Optional

from core.logger import get_logger
from .base_provider import TTSProvider, ProviderType
from .edge_tts_provider import EdgeTTSProvider
from .pyttsx3_provider import Pyttsx3Provider

logger = get_logger("tts.providers.manager")


class TTSProviderManager:
    """Manages TTS providers and implements fallback logic"""
    
    def __init__(self):
        """Initialize provider manager with available providers"""
        self._providers: Dict[str, TTSProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self) -> None:
        """Initialize all available TTS providers"""
        # Initialize Edge TTS (cloud, high quality - preferred)
        try:
            edge_provider = EdgeTTSProvider()
            if edge_provider.is_available():
                self._providers["edge_tts"] = edge_provider
                logger.info("Edge TTS provider initialized and available")
            else:
                logger.warning("Edge TTS provider not available")
        except Exception as e:
            logger.warning(f"Failed to initialize Edge TTS provider: {e}")
        
        # Initialize pyttsx3 (offline, fallback)
        try:
            pyttsx3_provider = Pyttsx3Provider()
            if pyttsx3_provider.is_available():
                self._providers["pyttsx3"] = pyttsx3_provider
                logger.info("pyttsx3 provider initialized and available")
            else:
                logger.warning("pyttsx3 provider not available")
        except Exception as e:
            logger.warning(f"Failed to initialize pyttsx3 provider: {e}")
        
        if not self._providers:
            logger.error("No TTS providers available!")
    
    def get_available_provider(self, preferred: Optional[str] = None) -> Optional[TTSProvider]:
        """Get an available provider, with optional preference.
        
        Args:
            preferred: Preferred provider name ("edge_tts" or "pyttsx3").
                      If None, returns first available provider (Edge TTS preferred).
        
        Returns:
            Available TTSProvider instance or None if none available
        """
        # If preferred provider is specified and available, return it
        if preferred and preferred in self._providers:
            provider = self._providers[preferred]
            if provider.is_available():
                return provider
        
        # Try Edge TTS first (cloud, high quality)
        if "edge_tts" in self._providers:
            provider = self._providers["edge_tts"]
            if provider.is_available():
                return provider
        
        # Fallback to pyttsx3 (offline)
        if "pyttsx3" in self._providers:
            provider = self._providers["pyttsx3"]
            if provider.is_available():
                return provider
        
        # No provider available
        return None
    
    def convert_with_fallback(
        self,
        text: str,
        voice: str,
        output_path: Path,
        preferred_provider: Optional[str] = None,
        rate: Optional[float] = None,
        pitch: Optional[float] = None,
        volume: Optional[float] = None
    ) -> bool:
        """Convert text to speech with automatic fallback.
        
        Tries preferred provider first, then falls back to other available providers.
        
        Args:
            text: Text to convert
            voice: Voice identifier (provider-specific)
            output_path: Path where audio file will be saved
            preferred_provider: Preferred provider name ("edge_tts" or "pyttsx3")
            rate: Speech rate adjustment
            pitch: Pitch adjustment
            volume: Volume adjustment
        
        Returns:
            True if conversion successful, False if all providers failed
        """
        # Build list of providers to try
        providers_to_try: List[tuple[str, TTSProvider]] = []
        
        # Add preferred provider first if specified
        if preferred_provider and preferred_provider in self._providers:
            provider = self._providers[preferred_provider]
            if provider.is_available():
                providers_to_try.append((preferred_provider, provider))
        
        # Add other available providers in fallback order
        # Edge TTS first (if not already added)
        if "edge_tts" in self._providers and preferred_provider != "edge_tts":
            provider = self._providers["edge_tts"]
            if provider.is_available():
                providers_to_try.append(("edge_tts", provider))
        
        # pyttsx3 as final fallback (if not already added)
        if "pyttsx3" in self._providers and preferred_provider != "pyttsx3":
            provider = self._providers["pyttsx3"]
            if provider.is_available():
                providers_to_try.append(("pyttsx3", provider))
        
        # Try each provider until one succeeds
        for provider_name, provider in providers_to_try:
            try:
                logger.info(f"Attempting TTS conversion with {provider_name}")
                success = provider.convert_text_to_speech(
                    text=text,
                    voice=voice,
                    output_path=output_path,
                    rate=rate,
                    pitch=pitch,
                    volume=volume
                )
                
                if success:
                    logger.info(f"TTS conversion successful with {provider_name}")
                    return True
                else:
                    logger.warning(f"TTS conversion failed with {provider_name}, trying fallback")
            except Exception as e:
                logger.warning(f"Error with {provider_name}: {e}, trying fallback")
                continue
        
        # All providers failed
        logger.error("All TTS providers failed to convert text to speech")
        return False
    
    def get_all_voices(self, locale: Optional[str] = None) -> List[Dict]:
        """Get all voices from all available providers.
        
        Args:
            locale: Optional locale filter (e.g., "en-US"). Defaults to "en-US" only.
        
        Returns:
            List of voice dictionaries from all providers
        """
        all_voices: List[Dict] = []
        
        for provider_name, provider in self._providers.items():
            if provider.is_available():
                try:
                    voices = provider.get_voices(locale)
                    # Ensure provider field is set
                    for voice in voices:
                        if "provider" not in voice:
                            voice["provider"] = provider_name
                    all_voices.extend(voices)
                except Exception as e:
                    logger.warning(f"Error getting voices from {provider_name}: {e}")
        
        # Sort by name
        all_voices.sort(key=lambda x: x.get("name", ""))
        return all_voices
    
    def get_voices_by_provider(self, provider: str, locale: Optional[str] = None) -> List[Dict]:
        """Get voices from a specific provider.
        
        Args:
            provider: Provider name ("edge_tts" or "pyttsx3")
            locale: Optional locale filter (e.g., "en-US"). Defaults to "en-US" only.
        
        Returns:
            List of voice dictionaries from the specified provider
        """
        if provider not in self._providers:
            logger.warning(f"Provider {provider} not found")
            return []
        
        provider_instance = self._providers[provider]
        if not provider_instance.is_available():
            logger.warning(f"Provider {provider} is not available")
            return []
        
        try:
            voices = provider_instance.get_voices(locale)
            # Ensure provider field is set
            for voice in voices:
                if "provider" not in voice:
                    voice["provider"] = provider
            return voices
        except Exception as e:
            logger.error(f"Error getting voices from {provider}: {e}")
            return []
    
    def get_voices_by_type(self, provider_type: ProviderType, locale: Optional[str] = None) -> List[Dict]:
        """Get voices from providers of a specific type.
        
        Args:
            provider_type: ProviderType.CLOUD or ProviderType.OFFLINE
            locale: Optional locale filter (e.g., "en-US"). Defaults to "en-US" only.
        
        Returns:
            List of voice dictionaries from providers of the specified type
        """
        voices: List[Dict] = []
        
        for provider_name, provider in self._providers.items():
            if provider.is_available() and provider.get_provider_type() == provider_type:
                try:
                    provider_voices = provider.get_voices(locale)
                    # Ensure provider field is set
                    for voice in provider_voices:
                        if "provider" not in voice:
                            voice["provider"] = provider_name
                    voices.extend(provider_voices)
                except Exception as e:
                    logger.warning(f"Error getting voices from {provider_name}: {e}")
        
        # Sort by name
        voices.sort(key=lambda x: x.get("name", ""))
        return voices
    
    def get_providers(self) -> List[str]:
        """Get list of available provider names.
        
        Returns:
            List of provider names that are available
        """
        return [
            name for name, provider in self._providers.items()
            if provider.is_available()
        ]
    
    def get_provider(self, provider_name: str) -> Optional[TTSProvider]:
        """Get a specific provider instance.
        
        Args:
            provider_name: Provider name ("edge_tts" or "pyttsx3")
        
        Returns:
            TTSProvider instance or None if not found/not available
        """
        if provider_name not in self._providers:
            return None
        
        provider = self._providers[provider_name]
        if not provider.is_available():
            return None
        
        return provider

