"""
Voice Resolver for TTS Module

Handles voice lookup, validation, and resolution with a clean pipeline approach.
Simplifies the complex voice management that was spread across VoiceManager and VoiceValidator.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import warnings

from core.config_manager import get_config
from core.logger import get_logger

from .providers.base_provider import TTSProvider
from .providers.provider_manager import TTSProviderManager

# Suppress deprecation warning for VoiceManager - VoiceResolver uses it internally
with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    from .voice_manager import VoiceManager

logger = get_logger("tts.voice_resolver")


@dataclass
class VoiceResolutionResult:
    """Result of voice resolution operation."""

    voice_id: str
    provider: TTSProvider
    voice_metadata: Dict[str, Any]
    fallback_used: bool = False


class VoiceNotFoundError(Exception):
    """Raised when a requested voice cannot be found."""

    pass


class VoiceResolver:
    """
    Handles voice resolution with a clean, simplified pipeline.

    Responsibilities:
    - Voice lookup and validation
    - Provider resolution
    - Fallback logic
    """

    def __init__(self, provider_manager: TTSProviderManager):
        """
        Initialize voice resolver.

        Args:
            provider_manager: TTS provider manager instance
        """
        self.provider_manager = provider_manager
        self.voice_manager = VoiceManager(provider_manager=provider_manager)
        self.config = get_config()

        logger.debug("VoiceResolver initialized")

    def resolve_voice(
        self, voice_name: Optional[str] = None, preferred_provider: Optional[str] = None
    ) -> VoiceResolutionResult:
        """
        Resolve voice name/id to a concrete voice and provider.

        Args:
            voice_name: Voice name, ID, or None for default
            preferred_provider: Preferred provider name or None for auto-selection

        Returns:
            VoiceResolutionResult with resolved voice information

        Raises:
            VoiceNotFoundError: If voice cannot be resolved
        """
        # Get voice name with config fallback
        voice_name = voice_name or self.config.get("tts.voice", "en-US-AndrewNeural")

        # Clean voice name
        voice_name = voice_name.strip()

        logger.debug(f"Resolving voice: '{voice_name}', preferred provider: {preferred_provider}")

        # Try exact match first with preferred provider
        if preferred_provider:
            result = self._try_resolve_with_provider(voice_name, preferred_provider)
            if result:
                return result

        # Try exact match with any provider
        result = self._try_resolve_any_provider(voice_name)
        if result:
            return result

        # Try fuzzy matching
        result = self._try_fuzzy_match(voice_name, preferred_provider)
        if result:
            return result

        # All resolution attempts failed
        available_voices = self.get_available_voices()
        logger.error(f"Voice '{voice_name}' not found. Available voices: {len(available_voices)}")
        if available_voices:
            logger.error("First 5 available voices:")
            for i, voice in enumerate(available_voices[:5]):
                logger.error(f"  {i+1}. {voice.get('name', 'unknown')} ({voice.get('id', 'no-id')})")

        raise VoiceNotFoundError(f"Voice '{voice_name}' not found in any provider")

    def _try_resolve_with_provider(self, voice_name: str, provider_name: str) -> Optional[VoiceResolutionResult]:
        """Try to resolve voice with a specific provider."""
        # Check if provider is available
        provider = self.provider_manager.get_provider(provider_name)
        if not provider:
            logger.debug(f"Preferred provider '{provider_name}' is not available")
            return None

        # Try to find voice in this provider
        voice_dict = self.voice_manager.get_voice_by_name(voice_name, provider=provider_name)
        if voice_dict:
            voice_id = self._extract_voice_id(voice_dict)
            logger.info(f"Resolved voice '{voice_name}' to '{voice_id}' using provider '{provider_name}'")
            return VoiceResolutionResult(voice_id=voice_id, provider=provider, voice_metadata=voice_dict)

        return None

    def _try_resolve_any_provider(self, voice_name: str) -> Optional[VoiceResolutionResult]:
        """Try to resolve voice with any available provider."""
        # Get all voices from all providers
        all_voices = self.voice_manager.get_voices()

        for voice_dict in all_voices:
            voice_id = self._extract_voice_id(voice_dict)
            provider_name = voice_dict.get("provider")

            # Check if this voice matches
            if self._voice_matches(voice_name, voice_dict):
                provider = self.provider_manager.get_provider(provider_name)
                if provider:
                    logger.info(f"Resolved voice '{voice_name}' to '{voice_id}' using provider '{provider_name}'")
                    return VoiceResolutionResult(voice_id=voice_id, provider=provider, voice_metadata=voice_dict)

        return None

    def _try_fuzzy_match(
        self, voice_name: str, preferred_provider: Optional[str] = None
    ) -> Optional[VoiceResolutionResult]:
        """Try fuzzy matching for voice names."""
        # Handle Windows SAPI voice names that might be selected in UI
        voice_name_lower = voice_name.lower()

        # Windows voice mapping
        windows_mappings = {
            "microsoft ana online (natural)": "en-US-AnaNeural",
            "microsoft zira desktop": "en-US-ZiraNeural",
            "microsoft david desktop": "en-US-ZiraNeural",  # Map male to female for consistency
            "microsoft aria online (natural)": "en-US-AriaNeural",
            "ana": "en-US-AnaNeural",
            "zira": "en-US-ZiraNeural",
            "aria": "en-US-AriaNeural",
        }

        # Check for Windows voice mappings
        for windows_name, edge_voice in windows_mappings.items():
            if windows_name in voice_name_lower:
                logger.info(f"Mapped Windows voice '{voice_name}' to Edge TTS voice '{edge_voice}'")
                return self.resolve_voice(edge_voice, preferred_provider)

        # Try partial matching
        all_voices = self.voice_manager.get_voices()
        voice_name_lower = voice_name.lower().strip()

        for voice_dict in all_voices:
            provider_name = voice_dict.get("provider")
            voice_name_full = (voice_dict.get("name") or "").lower()

            # Check partial matches
            if voice_name_lower in voice_name_full or voice_name_full.startswith(voice_name_lower):
                provider = self.provider_manager.get_provider(provider_name)
                if provider:
                    voice_id = self._extract_voice_id(voice_dict)
                    logger.info(f"Fuzzy matched voice '{voice_name}' to '{voice_id}' using provider '{provider_name}'")
                    return VoiceResolutionResult(
                        voice_id=voice_id, provider=provider, voice_metadata=voice_dict, fallback_used=True
                    )

        return None

    def _voice_matches(self, requested_name: str, voice_dict: Dict[str, Any]) -> bool:
        """Check if a voice dictionary matches the requested voice name."""
        requested_lower = requested_name.lower()

        # Check exact matches
        voice_id = (voice_dict.get("id") or "").lower()
        voice_name = (voice_dict.get("name") or "").lower()
        voice_short = (voice_dict.get("ShortName") or "").lower()

        return voice_id == requested_lower or voice_name == requested_lower or voice_short == requested_lower

    def _extract_voice_id(self, voice_dict: Dict[str, Any]) -> str:
        """Extract the voice ID from voice metadata."""
        return voice_dict.get("id") or voice_dict.get("ShortName") or voice_dict.get("name") or str(voice_dict)

    def get_available_voices(
        self, locale: Optional[str] = None, provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available voices with optional filtering.

        Args:
            locale: Optional locale filter (defaults to en-US)
            provider: Optional provider filter

        Returns:
            List of voice dictionaries
        """
        # Default to en-US locale
        if locale is None:
            locale = "en-US"

        return self.voice_manager.get_voices(locale=locale, provider=provider)

    def validate_voice_exists(self, voice_name: str, provider: Optional[str] = None) -> bool:
        """
        Check if a voice exists without resolving it.

        Args:
            voice_name: Voice name to check
            provider: Optional provider to check within

        Returns:
            True if voice exists, False otherwise
        """
        try:
            self.resolve_voice(voice_name, provider)
            return True
        except VoiceNotFoundError:
            return False
