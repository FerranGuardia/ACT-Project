"""
Voice validation and management module for TTS engine.

DEPRECATED: This module is deprecated. Use VoiceResolver instead.

Handles voice lookup, validation, ID resolution, and provider management.
"""

import warnings
from typing import Any, Dict, Optional

from core.config_manager import get_config
from core.logger import get_logger

from .providers.base_provider import TTSProvider
from .providers.provider_manager import TTSProviderManager
from .voice_manager import VoiceManager

logger = get_logger("tts.voice_validator")

# Deprecation warning
warnings.warn("VoiceValidator is deprecated. Use VoiceResolver instead.", DeprecationWarning, stacklevel=2)


class VoiceValidator:
    """Handles voice validation and resolution."""

    def __init__(self, voice_manager: VoiceManager, provider_manager: TTSProviderManager):
        """
        Initialize voice validator.

        Args:
            voice_manager: VoiceManager instance for voice lookups
            provider_manager: TTSProviderManager for provider access
        """
        self.voice_manager = voice_manager
        self.provider_manager = provider_manager
        self.config = get_config()

    def get_available_voices(
        self, locale: Optional[str] = None, provider: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Get list of available voices.

        Args:
            locale: Optional locale filter (e.g., "en-US")
            provider: Optional provider name ("edge_tts" or "pyttsx3")

        Returns:
            List of voice dictionaries
        """
        return self.voice_manager.get_voices(locale=locale, provider=provider)  # type: ignore[return-value, arg-type]

    def validate_and_resolve_voice(
        self, voice: Optional[str], provider: Optional[str]
    ) -> Optional[tuple[str, Optional[str], Dict[str, Any]]]:
        """
        Validate and resolve voice parameters.

        Handles:
        - Voice lookup and ID resolution
        - Provider validation and fallback logic
        - Locale and gender extraction for logging

        Args:
            voice: Voice ID or name (e.g., "en-US-AndrewNeural"). If None, uses config default.
            provider: Optional provider name ("edge_tts" or "pyttsx3").

        Returns:
            Tuple of (voice_id: str, resolved_provider: Optional[str], voice_dict: Dict[str, Any])
            or None if voice validation fails
        """
        # Get voice with config fallback
        if voice is None:
            voice = self.config.get("tts.voice", "en-US-AndrewNeural")

        # Clean voice name (remove any extra formatting)
        if voice is not None:
            voice = voice.strip()
        else:
            voice = "en-US-AndrewNeural"  # Fallback if config returns None

        # Handle Windows SAPI voice names that might be selected in UI
        # Map common Windows TTS voice names to Edge TTS equivalents
        windows_voice_mapping = {
            # Ana voices
            "microsoft ana online (natural)": "en-US-AnaNeural",
            "microsoft ana online (natural) - english (united states) female": "en-US-AnaNeural",
            "microsoft ana online (natural) - english (united states)": "en-US-AnaNeural",
            # Zira voices
            "microsoft zira desktop": "en-US-ZiraNeural",
            "microsoft zira desktop - english (united states)": "en-US-ZiraNeural",
            # David voices
            "microsoft david desktop": "en-US-ZiraNeural",  # Map to female since David is male but we want consistency
            "microsoft david desktop - english (united states)": "en-US-ZiraNeural",
            # Aria voices (if available)
            "microsoft aria online (natural)": "en-US-AriaNeural",
            "microsoft aria online (natural) - english (united states)": "en-US-AriaNeural",
            # Generic mappings for common patterns
            "ana": "en-US-AnaNeural",
            "zira": "en-US-ZiraNeural",
            "aria": "en-US-AriaNeural",
        }

        # Check if the voice name matches any Windows voice patterns
        voice_lower = voice.lower()
        for windows_name, edge_voice in windows_voice_mapping.items():
            if windows_name in voice_lower:
                logger.info(f"Mapped Windows voice '{voice}' to Edge TTS voice '{edge_voice}'")
                voice = edge_voice
                break

        # Ensure voice is a string at this point
        if not isinstance(voice, str):
            logger.error(f"Invalid voice type: {type(voice)}")
            return None

        # Validate provider if specified
        provider_instance: Optional[TTSProvider] = self._get_provider_instance(provider)
        if provider and not provider_instance:
            # Provider was specified but not available
            logger.error(f"Provider '{provider}' was specified but not available")
            return None

        # Look up voice in provider(s)
        logger.debug(f"Looking up voice '{voice}' in provider '{provider or 'any'}'")
        # Suppress warnings about partially unknown return type from VoiceManager
        voice_dict: Optional[Dict[str, Any]] = self.voice_manager.get_voice_by_name(voice, provider=provider)  # type: ignore[assignment]
        if not voice_dict:
            if provider:
                # If provider is specified and voice not found, fail (no fallback)
                logger.error(f"Voice '{voice}' not found in provider '{provider}' - available voices may not be loaded")
                return None
            else:
                # If no provider specified, try to find voice in any provider
                logger.warning(f"Voice '{voice}' not found, searching all providers...")
                # Suppress warnings about partially unknown return type from VoiceManager
                voice_dict = self.voice_manager.get_voice_by_name(voice, provider=None)  # type: ignore[assignment]
                if not voice_dict:
                    logger.error(
                        f"Voice '{voice}' not found in any provider - voice manager may not be initialized properly"
                    )
                    # Log available voices for debugging
                    try:
                        all_voices = self.voice_manager.get_voices()
                        logger.error(f"Available voices ({len(all_voices)} total):")
                        for i, v in enumerate(all_voices[:5]):  # Show first 5
                            logger.error(f"  {i+1}. {v.get('name', 'unknown')} ({v.get('id', 'no-id')})")
                        if len(all_voices) > 5:
                            logger.error(f"  ... and {len(all_voices) - 5} more")
                    except Exception as e:
                        logger.error(f"Could not list available voices: {e}")
                    return None

        # Determine provider from voice metadata if not already specified
        resolved_provider = provider

        # Resolve voice ID (prefer id, then ShortName for backward compatibility)
        # Type ignore because voice_dict is Dict[str, Any] but Pylance sees Dict[Unknown, Unknown]
        voice_id_raw = voice_dict.get("id") or voice_dict.get("ShortName", voice)  # type: ignore[arg-type]
        voice_id: str = str(voice_id_raw) if voice_id_raw is not None else voice
        if voice_id != voice:
            logger.info(f"Resolved voice: '{voice}' -> '{voice_id}' (provider: {resolved_provider})")
        else:
            logger.info(f"Using voice: '{voice_id}' (provider: {resolved_provider})")
        if resolved_provider is None and "provider" in voice_dict:
            provider_value = voice_dict.get("provider")  # type: ignore[arg-type]
            if isinstance(provider_value, str):
                resolved_provider = provider_value
                # Validate the provider from metadata
                metadata_provider_instance = self._get_provider_instance(resolved_provider)
                if not metadata_provider_instance:
                    logger.warning(
                        f"Provider '{resolved_provider}' from voice metadata is not available, will use fallback"
                    )
                    resolved_provider = None
                else:
                    logger.info(f"Using provider '{resolved_provider}' from voice metadata")

        # Extract and log locale and gender
        # Type ignore because voice_dict is Dict[str, Any] but Pylance sees Dict[Unknown, Unknown]
        locale_raw = voice_dict.get("language") or voice_dict.get("Locale", "unknown")  # type: ignore[arg-type]
        gender_raw = voice_dict.get("gender") or voice_dict.get("Gender", "unknown")  # type: ignore[arg-type]
        locale_value: str = str(locale_raw) if locale_raw is not None else "unknown"
        gender_value: str = str(gender_raw) if gender_raw is not None else "unknown"
        logger.info(f"Voice '{voice_id}' validated successfully (Locale: {locale_value}, Gender: {gender_value})")

        return voice_id, resolved_provider, voice_dict

    def _get_provider_instance(self, provider: Optional[str]) -> Optional[TTSProvider]:
        """
        Get a provider instance for the specified provider name.

        Args:
            provider: Provider name (e.g., "edge_tts"). If None, returns None.

        Returns:
            TTSProvider instance or None if provider is unavailable
        """
        if not provider:
            return None

        instance = self.provider_manager.get_provider(provider)
        if not instance:
            logger.error(f"Provider '{provider}' is not available")
        return instance
